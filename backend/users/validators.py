from django.core.validators import RegexValidator

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Username может содержать только буквы, цифры, "._@", "+", и "-".'
)
