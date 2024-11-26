from django.core.validators import RegexValidator


tag_slug_validator = RegexValidator(
    regex=r'^[-a-zA-Z0-9_]+$',
    message=(
        'Slug может содержать только буквы, цифры,'
        'символы ".", "_", "@", "+", и "-".'
    )
)
