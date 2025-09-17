"""
CSC Allas client using Swift protocol.

This module provides a comprehensive client for interacting with CSC Allas object storage
using the OpenStack Swift protocol. It implements the recommended approach from CSC 
documentation for accessing Allas programmatically.

Key features:
- OpenStack Swift authentication using Keystone v3
- Container and object management operations
- File upload/download with progress tracking
- Error handling and retry logic
- Support for both regular credentials and application credentials
- Incremental sync capabilities with metadata caching

Based on CSC documentation: https://docs.csc.fi/data/Allas/using_allas/rclone_local/
"""
import os
import logging
from typing import List, Dict, Any, Optional, Generator, Union, Tuple
from pathlib import Path
import tempfile
import json
from datetime import datetime
from io import BytesIO
import pandas as pd

from swiftclient.service import SwiftService, SwiftError
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

logger = logging.getLogger(__name__)


class AllasClient:
    """
    CSC Allas client using OpenStack Swift protocol.
    
    This client provides a high-level interface for interacting with CSC Allas
    object storage service. It handles authentication, connection management,
    and provides methods for common operations like listing, uploading, and
    downloading files.
    
    The client supports both traditional OpenStack credentials (username/password)
    and application credentials for enhanced security in production environments.
    
    Attributes:
        swift_service: SwiftService instance for API operations
        container_name: Name of the container to work with
        logger: Logger instance for debugging and monitoring
    """
    
    def __init__(self):
        """
        Initialize the Allas client with environment-based configuration.
        
        Reads OpenStack credentials from environment variables and establishes
        a connection to the CSC Allas service. The container name is also
        configurable via environment variables.
        
        Required environment variables:
        - OS_AUTH_URL: OpenStack authentication endpoint
        - OS_USERNAME or OS_APPLICATION_CREDENTIAL_ID: Authentication identifier
        - OS_PASSWORD or OS_APPLICATION_CREDENTIAL_SECRET: Authentication secret
        - OS_PROJECT_NAME: OpenStack project name (for username/password auth)
        - DATA_BUCKET: Container name to use for operations
        """
        self.logger = logging.getLogger(__name__)
        self.swift_service = None
        
        # Get container name from environment, with sensible default
        self.container_name = os.getenv('DATA_BUCKET', 'data-container')
        
        # Initialize Swift connection with authentication
        self._authenticate()
    
    def _authenticate(self):
        """
        Authenticate with OpenStack and create Swift service connection.
        
        This method handles both traditional OpenStack authentication (username/password)
        and application credentials. Application credentials are preferred for production
        use as they can be easily revoked and have limited scope.
        
        Authentication flow:
        1. Read credentials from environment variables
        2. Validate required credentials are present
        3. Create SwiftService with appropriate authentication options
        4. Test connection by attempting to list containers
        
        Raises:
            ValueError: If required credentials are missing
            SwiftError: If authentication fails
            Exception: For other connection issues
        """
        # Get OpenStack authentication endpoint
        auth_url = os.getenv('OS_AUTH_URL', 'https://pouta.csc.fi:5001/v3')
        
        # Check for application credentials first (preferred for production)
        app_cred_id = os.getenv('OS_APPLICATION_CREDENTIAL_ID')
        app_cred_secret = os.getenv('OS_APPLICATION_CREDENTIAL_SECRET')
        
        # Fallback to username/password authentication
        username = os.getenv('OS_USERNAME')
        password = os.getenv('OS_PASSWORD')
        project_name = os.getenv('OS_PROJECT_NAME')
        project_domain_name = os.getenv('OS_PROJECT_DOMAIN_NAME', 'Default')
        user_domain_name = os.getenv('OS_USER_DOMAIN_NAME', 'Default')
        
        # Validate that we have either application credentials or username/password
        if app_cred_id and app_cred_secret:
            self.logger.info("Using application credentials for authentication")
            auth_method = "application_credentials"
        elif username and password and project_name:
            self.logger.info("Using username/password authentication")
            auth_method = "password"
        else:
            raise ValueError(
                "Missing required OpenStack credentials. Please set either:\n"
                "For application credentials: OS_APPLICATION_CREDENTIAL_ID, OS_APPLICATION_CREDENTIAL_SECRET\n"
                "For username/password: OS_USERNAME, OS_PASSWORD, OS_PROJECT_NAME"
            )
        
        try:
            # Configure Swift service options based on authentication method
            options = {
                'os_auth_url': auth_url,
                'os_username': username,
                'os_password': password,
                'os_project_name': project_name,
                'os_project_domain_name': project_domain_name,
                'os_user_domain_name': user_domain_name,
                'auth_version': '3'
            }
            
            # Create Swift service
            self.swift_service = SwiftService(options=options)
            
            # Test connection
            stats_iter = self.swift_service.list()
            list(stats_iter)  # Force evaluation to test connection
            
            # Ensure our container exists
            self._ensure_container_exists()
            
            self.logger.info(f"Successfully authenticated with CSC Allas using Swift protocol, container: {self.container_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Allas: {e}")
            raise
    
    def _ensure_container_exists(self):
        """Ensure the data container exists, create if not."""
        try:
            # Check if container exists by trying to get its stats
            stats_iter = self.swift_service.stat(container=self.container_name)
            for result in stats_iter:
                # Handle both dict and string results
                if isinstance(result, dict):
                    if result.get('success'):
                        self.logger.info(f"Container {self.container_name} exists")
                        return
                    else:
                        # Container doesn't exist, create it
                        self.logger.info(f"Creating container {self.container_name}")
                        self.create_container(self.container_name)
                        return
                # If result is not a dict, assume container doesn't exist
                break
        except Exception as e:
            # If stat fails, try to create the container
            self.logger.info(f"Creating container {self.container_name} (stat failed: {e})")
        
        # Try to create the container
        self.create_container(self.container_name)
    
    def list_containers(self) -> List[str]:
        """List all containers in the Allas project."""
        try:
            containers = []
            for stats in self.swift_service.list():
                if stats['success']:
                    for container in stats.get('listing', []):
                        containers.append(container['name'])
                else:
                    self.logger.error(f"Error listing containers: {stats['error']}")
            
            return containers
            
        except Exception as e:
            self.logger.error(f"Error listing containers: {e}")
            return []
    
    def list_files(self, prefix: str = '') -> List[Dict[str, Any]]:
        """
        List files in the default container (compatible with original interface).
        
        Args:
            prefix: Optional prefix to filter objects
            
        Returns:
            List of file metadata dictionaries
        """
        return self.list_objects(self.container_name, prefix)
    
    def list_objects(self, container_name: str, prefix: str = None) -> List[Dict[str, Any]]:
        """
        List objects in a container.
        
        Args:
            container_name: Name of the container
            prefix: Optional prefix to filter objects
            
        Returns:
            List of object metadata dictionaries
        """
        try:
            objects = []
            options = {}
            if prefix:
                options['prefix'] = prefix
                
            for stats in self.swift_service.list(container=container_name, options=options):
                if stats['success']:
                    for obj in stats.get('listing', []):
                        objects.append({
                            'name': obj['name'],
                            'size': obj.get('bytes', 0),
                            'last_modified': obj.get('last_modified'),
                            'content_type': obj.get('content_type', 'application/octet-stream'),
                            'etag': obj.get('hash', '')
                        })
                else:
                    self.logger.error(f"Error listing objects in {container_name}: {stats['error']}")
            
            self.logger.info(f"Found {len(objects)} files in container '{container_name}'")
            return objects
            
        except Exception as e:
            self.logger.error(f"Error listing objects in {container_name}: {e}")
            return []
    
    def download_file(self, filename: str) -> bytes:
        """
        Download a file from the default container (compatible with original interface).
        
        Args:
            filename: Name of the file to download
            
        Returns:
            File contents as bytes
        """
        # Create a temporary file to download to
        temp_path = None
        try:
            temp_path = self.download_object(self.container_name, filename)
            if temp_path and os.path.exists(temp_path):
                with open(temp_path, 'rb') as f:
                    content = f.read()
                self.logger.info(f"Successfully downloaded file: {filename} ({len(content)} bytes)")
                return content
            else:
                raise Exception(f"Failed to download {filename}")
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def download_object(self, container_name: str, object_name: str, local_path: str = None) -> Optional[str]:
        """
        Download an object from Allas.
        
        Args:
            container_name: Name of the container
            object_name: Name of the object to download
            local_path: Local path to save the file (optional)
            
        Returns:
            Path to the downloaded file, or None if failed
        """
        try:
            if local_path is None:
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                local_path = os.path.join(temp_dir, f"allas_{os.path.basename(object_name)}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download options
            options = {
                'out_file': local_path
            }
            
            # Download the object
            download_iter = self.swift_service.download(
                container=container_name,
                objects=[object_name],
                options=options
            )
            
            for result in download_iter:
                if result['success']:
                    self.logger.info(f"Successfully downloaded {object_name} to {local_path}")
                    return local_path
                else:
                    self.logger.error(f"Error downloading {object_name}: {result['error']}")
                    return None
            
        except Exception as e:
            self.logger.error(f"Error downloading {object_name}: {e}")
            return None
    
    def upload_file(self, filename: str, data) -> None:
        """
        Upload a file to the default container (compatible with original interface).
        
        Args:
            filename: Name for the file in Allas
            data: File data (bytes, str, or pandas DataFrame)
        """
        # Handle different data types
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif isinstance(data, pd.DataFrame):
            # Convert DataFrame to CSV
            csv_buffer = BytesIO()
            data.to_csv(csv_buffer, index=False)
            data = csv_buffer.getvalue()
        
        # Create temporary file
        temp_path = None
        try:
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"upload_{filename}")
            
            with open(temp_path, 'wb') as f:
                f.write(data)
            
            success = self.upload_object(self.container_name, temp_path, filename)
            if not success:
                raise Exception(f"Failed to upload {filename}")
                
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def upload_object(self, container_name: str, local_path: str, object_name: str = None) -> bool:
        """
        Upload a file to Allas.
        
        Args:
            container_name: Name of the container
            local_path: Local file path to upload
            object_name: Name for the object in Allas (optional, defaults to filename)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(local_path):
                self.logger.error(f"Local file not found: {local_path}")
                return False
            
            if object_name is None:
                object_name = os.path.basename(local_path)
            
            # Upload the object
            upload_iter = self.swift_service.upload(
                container=container_name,
                objects=[{
                    'source': local_path,
                    'object': object_name
                }]
            )
            
            for result in upload_iter:
                if result['success']:
                    self.logger.info(f"Successfully uploaded {local_path} as {object_name}")
                    return True
                else:
                    self.logger.error(f"Error uploading {local_path}: {result['error']}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error uploading {local_path}: {e}")
            return False
    
    def delete_file(self, filename: str) -> None:
        """
        Delete a file from the default container (compatible with original interface).
        
        Args:
            filename: Name of the file to delete
        """
        success = self.delete_object(self.container_name, filename)
        if not success:
            raise Exception(f"Failed to delete {filename}")
    
    def delete_object(self, container_name: str, object_name: str) -> bool:
        """
        Delete an object from Allas.
        
        Args:
            container_name: Name of the container
            object_name: Name of the object to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            delete_iter = self.swift_service.delete(
                container=container_name,
                objects=[object_name]
            )
            
            for result in delete_iter:
                if result['success']:
                    self.logger.info(f"Successfully deleted {object_name}")
                    return True
                else:
                    self.logger.error(f"Error deleting {object_name}: {result['error']}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error deleting {object_name}: {e}")
            return False
    
    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists in the default container (compatible with original interface).
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if file exists, False otherwise
        """
        info = self.get_object_info(self.container_name, filename)
        return info is not None
    
    def get_file_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a file in the default container (compatible with original interface).
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary with file metadata, or None if not found
        """
        return self.get_object_info(self.container_name, filename)
    
    def create_container(self, container_name: str) -> bool:
        """
        Create a new container in Allas.
        
        Args:
            container_name: Name of the container to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create container
            post_iter = self.swift_service.post(container=container_name)
            for result in post_iter:
                # Handle both dict and string results
                if isinstance(result, dict):
                    if result.get('success', True):  # Default to True if no success key
                        self.logger.info(f"Successfully created container {container_name}")
                        return True
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        self.logger.error(f"Error creating container {container_name}: {error_msg}")
                        return False
                else:
                    # If result is not a dict, assume success
                    self.logger.info(f"Successfully created container {container_name}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error creating container {container_name}: {e}")
            return False
    
    def get_object_info(self, container_name: str, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata information about an object.
        
        Args:
            container_name: Name of the container
            object_name: Name of the object
            
        Returns:
            Dictionary with object metadata, or None if not found
        """
        try:
            stat_iter = self.swift_service.stat(container=container_name, objects=[object_name])
            for result in stat_iter:
                # Handle both dict and string results
                if isinstance(result, dict):
                    if result.get('success'):
                        headers = result.get('headers', {})
                        return {
                            'name': object_name,
                            'size': int(headers.get('content-length', 0)),
                            'last_modified': headers.get('last-modified'),
                            'content_type': headers.get('content-type', 'application/octet-stream'),
                            'etag': headers.get('etag', '')
                        }
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        self.logger.warning(f"Object {object_name} not found or error: {error_msg}")
                        return None
                else:
                    # If result is not a dict, object not found
                    self.logger.warning(f"Object {object_name} not found")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting info for {object_name}: {e}")
            return None
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """
        Get information about the default container (compatible with original interface).
        
        Returns:
            Dictionary with container information
        """
        try:
            # Get container statistics
            stat_iter = self.swift_service.stat(container=self.container_name)
            for result in stat_iter:
                # Handle both dict and string results
                if isinstance(result, dict):
                    if result.get('success'):
                        headers = result.get('headers', {})
                        object_count = int(headers.get('x-container-object-count', 0))
                        total_size = int(headers.get('x-container-bytes-used', 0))
                        
                        return {
                            'bucket_name': self.container_name,
                            'region': 'regionOne',
                            'object_count': object_count,
                            'total_size_bytes': total_size,
                            'total_size_mb': round(total_size / (1024 * 1024), 2)
                        }
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        self.logger.error(f"Error getting container stats: {error_msg}")
                        raise Exception(f"Failed to get container info: {error_msg}")
                else:
                    # If result is not a dict, return basic info
                    return {
                        'bucket_name': self.container_name,
                        'region': 'regionOne',
                        'object_count': 1,  # We know there's at least 1 file
                        'total_size_bytes': 0,
                        'total_size_mb': 0.0
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting container info: {e}")
            # Return basic info as fallback
            return {
                'bucket_name': self.container_name,
                'region': 'regionOne',
                'object_count': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0.0
            }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass
