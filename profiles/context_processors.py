def guest_status_processor(request):
    """
    Menyuntikkan variabel global 'is_guest_account' ke semua template.
    """
    is_guest = False
    
    # Cek apakah user login
    if request.user.is_authenticated:
        # Cek apakah punya profile dan apakah dia guest
        if hasattr(request.user, 'profile') and request.user.profile.is_guest:
            is_guest = True
            
    # Return dictionary (ini akan digabung dengan context template)
    return {
        'is_guest_account': is_guest
    }