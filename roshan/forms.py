from django import forms
from .models import ResourceCategory, Resource, ManualPlaylist, ManualTrack


class ResourceFilterForm(forms.Form):
    """Form for filtering resources on the resources page."""

    SORT_CHOICES = [
        ("newest", "Newest First"),
        ("oldest", "Oldest First"),
        ("rating", "Highest Rated"),
        ("title", "Title A-Z"),
    ]

    category = forms.ModelChoiceField(
        queryset=ResourceCategory.objects.all(),
        empty_label="All Categories",
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "categoryFilter"}),
    )

    type = forms.ChoiceField(
        choices=[("all", "All Types")] + list(Resource.ResourceType.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "typeFilter"}),
    )

    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search resources...",
                "id": "searchInput",
            }
        ),
    )

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial="newest",
        widget=forms.Select(attrs={"class": "form-control", "id": "sortFilter"}),
    )


# =========================================================================
# PLAYLIST FORMS
# =========================================================================


class ManualPlaylistForm(forms.ModelForm):
    """Form for creating and editing manual playlists"""

    class Meta:
        model = ManualPlaylist
        fields = ["name", "description", "cover_image", "is_public", "is_featured"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter playlist name...",
                    "required": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe your playlist...",
                    "rows": 3,
                }
            ),
            "cover_image": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ManualTrackForm(forms.ModelForm):
    """Form for adding tracks to manual playlists"""

    duration_minutes = forms.IntegerField(
        min_value=0,
        max_value=59,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
    )
    duration_seconds = forms.IntegerField(
        min_value=0,
        max_value=59,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
    )

    class Meta:
        model = ManualTrack
        fields = [
            "name",
            "artist",
            "album",
            "audio_file",
            "youtube_url",
            "apple_music_url",
            "track_number",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Track name...",
                    "required": True,
                }
            ),
            "artist": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Artist name...",
                    "required": True,
                }
            ),
            "album": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Album name (optional)...",
                }
            ),
            "audio_file": forms.FileInput(
                attrs={"class": "form-control", "accept": "audio/*"}
            ),
            "youtube_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://youtube.com/watch?v=...",
                }
            ),
            "apple_music_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://music.apple.com/...",
                }
            ),
            "track_number": forms.NumberInput(
                attrs={"class": "form-control", "min": "1"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Convert minutes and seconds to milliseconds
        minutes = cleaned_data.get("duration_minutes", 0)
        seconds = cleaned_data.get("duration_seconds", 0)

        if minutes or seconds:
            total_seconds = (minutes * 60) + seconds
            cleaned_data["duration_ms"] = total_seconds * 1000

        # Check that at least one audio source is provided
        audio_file = cleaned_data.get("audio_file")
        youtube_url = cleaned_data.get("youtube_url")

        if not audio_file and not youtube_url:
            raise forms.ValidationError(
                "Please provide either an audio file or a YouTube URL for playback."
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set duration_ms from the converted value
        if hasattr(self, "cleaned_data") and "duration_ms" in self.cleaned_data:
            instance.duration_ms = self.cleaned_data["duration_ms"]

        if commit:
            instance.save()
        return instance
