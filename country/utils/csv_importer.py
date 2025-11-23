def import_from_csv(model_key: str, file_obj, dry_run: bool = False):
    config = IMPORT_CONFIGS[model_key]
    model = config.model

    # If request.FILES object, decode to text
    if hasattr(file_obj, "read"):
        text = file_obj.read().decode("utf-8")
        from io import StringIO
        file_obj = StringIO(text)

    import csv
    reader = csv.DictReader(file_obj)

    created = 0
    updated = 0
    errors = []

    from django.db import transaction

    @transaction.atomic
    def _execute():
        nonlocal created, updated
        for line_num, row in enumerate(reader, start=2):
            try:
                # VALIDATIONS (optional)
                if hasattr(config, "validator"):
                    config.validator(row)

                attrs = {}

                # Simple mappings
                for csv_col, model_field in config.field_mapping.items():
                    value = row.get(csv_col)
                    if value not in [None, ""]:
                        attrs[model_field] = value

                # FKs
                for fk in getattr(config, "fk_mappings", []):
                    fk_value = row.get(fk.csv_column)
                    if fk_value:
                        target = fk.target_model.objects.get(
                            **{fk.target_lookup: fk_value}
                        )
                        attrs[fk.model_field] = target

                lookup_kwargs = {
                    field: attrs[field]
                    for field in config.natural_key_fields
                    if field in attrs
                }

                defaults = {
                    k: v for k, v in attrs.items()
                    if k not in config.natural_key_fields
                }

                obj, created_flag = model.objects.update_or_create(
                    **lookup_kwargs, defaults=defaults
                )

                created += int(created_flag)
                updated += int(not created_flag)

            except Exception as e:
                errors.append({"line": line_num, "row": row, "error": str(e)})

    _execute()

    return {
        "created": created,
        "updated": updated,
        "errors": errors
    }
