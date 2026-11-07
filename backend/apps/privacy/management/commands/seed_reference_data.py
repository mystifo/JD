"""Seed reference content (emotions, triggers, prompts, calm activities, resources).

The command is intentionally a skeleton in M1: seeders register themselves in
SEEDERS and each is idempotent (upsert by natural key). Missing modules are
reported, not silently ignored, so a later milestone cannot forget one.
"""

from importlib import import_module

from django.core.management.base import BaseCommand

SEEDERS = [
    ("apps.wellness.reference_data", "seed_emotions"),
    ("apps.wellness.reference_data", "seed_triggers"),
    ("apps.journal.reference_data", "seed_prompts"),
    ("apps.calm_space.reference_data", "seed_calm_content"),
    ("apps.privacy.reference_data", "seed_support_resources"),
]


class Command(BaseCommand):
    help = "Idempotently load reference content used by the product."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Fail when a seeder module has not been implemented yet.",
        )

    def handle(self, *args, **options):
        pending = []
        ran = 0
        for module_path, function_name in SEEDERS:
            try:
                module = import_module(module_path)
            except ModuleNotFoundError:
                pending.append(f"{module_path}.{function_name}")
                continue
            seeder = getattr(module, function_name, None)
            if seeder is None:
                pending.append(f"{module_path}.{function_name}")
                continue
            seeder()
            ran += 1
            self.stdout.write(self.style.SUCCESS(f"seeded {function_name}"))

        if pending:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(pending)} seeder(s) not implemented yet: {', '.join(pending)}"
                )
            )
            if options["strict"]:
                raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(f"reference data ready ({ran} seeder(s) run)"))
