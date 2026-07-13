from storages.backends.s3 import S3Storage

class SupabasePublicStaticStorage(S3Storage):
    """
    Forces django-storages to output clean, unauthenticated public Supabase URLs
    and explicitly maintains the target subfolder location pathway.
    """
    def url(self, name, parameters=None, expire=None, http_method=None):
        # Explicitly clean the name path
        clean_name = name.replace('\\', '/')
        
        # Remove the /s3 endpoint suffix to get the base domain path
        endpoint = self.endpoint_url.replace("/storage/v1/s3", "")
        bucket = self.bucket_name
        
        # Pull the location prefix ('static') safely if configured
        location_prefix = f"{self.location}/" if self.location else ""
        
        # Build the exact public object path structure including the folder location
        return f"{endpoint}/storage/v1/object/public/{bucket}/{location_prefix}{clean_name}"
