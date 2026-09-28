import os
from urllib.request import urlopen

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from cloudinary.exceptions import NotFound
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "avif"}


@deconstructible
class CloudinaryMediaStorage(Storage):
    """
    Media storage on Cloudinary that keeps Django's file names unchanged.

    A file saved as "wines/image_3.jpg" is stored on Cloudinary with the
    public ID "media/wines/image_3" and the database keeps
    "wines/image_3.jpg". Credentials are read by the cloudinary package
    from the CLOUDINARY_URL environment variable.
    """

    def __init__(self, folder="media"):
        self.folder = folder.strip("/")

    def _resource(self, name):
        """Return (public_id, resource_type, format) for a file name."""
        name = name.replace("\\", "/").lstrip("/")
        base, extension = os.path.splitext(name)
        extension = extension.lstrip(".").lower()
        prefix = f"{self.folder}/" if self.folder else ""
        if extension in IMAGE_EXTENSIONS:
            return prefix + base, "image", extension
        return prefix + name, "raw", None

    def _save(self, name, content):
        name = name.replace("\\", "/")
        public_id, resource_type, _ = self._resource(name)
        content.seek(0)
        cloudinary.uploader.upload(
            content,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=True,
            invalidate=True,
        )
        return name

    def _open(self, name, mode="rb"):
        with urlopen(self.url(name)) as response:
            return ContentFile(response.read(), name=name)

    def delete(self, name):
        public_id, resource_type, _ = self._resource(name)
        cloudinary.uploader.destroy(
            public_id, resource_type=resource_type, invalidate=True
        )

    def exists(self, name):
        public_id, resource_type, _ = self._resource(name)
        try:
            cloudinary.api.resource(public_id, resource_type=resource_type)
        except NotFound:
            return False
        return True

    def size(self, name):
        public_id, resource_type, _ = self._resource(name)
        resource = cloudinary.api.resource(
            public_id, resource_type=resource_type
        )
        return resource["bytes"]

    def url(self, name):
        public_id, resource_type, file_format = self._resource(name)
        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type=resource_type,
            format=file_format,
            secure=True,
        )
        return url
