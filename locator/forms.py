from django import forms

class UploadDatasetForm(forms.Form):
    """
    Form to handle the emergency dataset TXT file upload.
    """
    dataset_file = forms.FileField(
        label="Select Dataset File",
        help_text="Upload a plain text (.txt) dataset file under 2MB.",
        required=True
    )
