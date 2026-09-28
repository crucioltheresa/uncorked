from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Upload every file in the local media folder to the default "
        "storage, keeping the same names the database uses and "
        "overwriting files that already exist."
    )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.is_dir():
            raise CommandError(f"Media folder not found: {media_root}")
        if isinstance(default_storage, FileSystemStorage):
            raise CommandError(
                "The default storage is the local media folder. "
                "Set CLOUDINARY_URL to upload to Cloudinary."
            )

        files = sorted(p for p in media_root.rglob("*") if p.is_file())
        for path in files:
            name = path.relative_to(media_root).as_posix()
            if default_storage.exists(name):
                default_storage.delete(name)
            with path.open("rb") as handle:
                saved_name = default_storage.save(name, File(handle, name))
            if saved_name != name:
                raise CommandError(
                    f"{name} was saved as {saved_name}; names must match."
                )
            self.stdout.write(f"{name} -> {default_storage.url(name)}")

        self.stdout.write(
            self.style.SUCCESS(f"Uploaded {len(files)} file(s).")
        )
