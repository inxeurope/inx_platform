def server_status(request):
    is_local = False
    if 'localhost' in request.get_host() or '127.0.0.1' in request.get_host():
        is_local = True
    return {'is_local': is_local}