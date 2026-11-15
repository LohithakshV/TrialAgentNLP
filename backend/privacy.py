def clean_profile(profile):
    """Trim fields to the same bounds used by the request schema."""
    return type(profile)(
        condition=profile.condition[:160],
        stage=profile.stage[:80],
        biomarkers=[biomarker[:180] for biomarker in profile.biomarkers][:12],
        city=profile.city[:100],
    )
