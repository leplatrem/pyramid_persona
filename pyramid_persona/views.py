import logging
import pkg_resources
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.response import Response
from pyramid.security import remember, forget
import browserid.errors


logger = logging.getLogger(__name__)


def verify_login(request):
    """Verifies the assertion and the csrf token in the given request.

    Returns the email of the user if everything is valid, otherwise raises
    a HTTPBadRequest"""
    verifier = request.registry['persona.verifier']
    try:
        data = verifier.verify(request.POST['assertion'])
    except (ValueError, browserid.errors.TrustError) as e:
        logger.info('Failed persona login: %s (%s)', e, type(e).__name__)
        raise HTTPBadRequest('Invalid assertion')
    return data['email']


def add_csrf_token(request):
    """Provides the CSRF token in HTTP headers."""
    csrf_token = str(request.session.get_csrf_token())
    request.response.headers['X-Csrf-Token'] = csrf_token
    return csrf_token


def login(request):
    """View to check the persona assertion and remember the user"""
    add_csrf_token(request)
    if request.method == 'POST':
        email = verify_login(request)
        request.response.headers.extend(remember(request, email))
        return {'redirect': request.POST.get('came_from', '/'), 'success': True}
    return {}


def logout(request):
    """View to forget the user"""
    add_csrf_token(request)
    request.response.headers.extend(forget(request))
    return {'redirect': request.POST.get('came_from', '/')}


def forbidden(request):
    """A basic 403 view, with a login button"""
    template = pkg_resources.resource_string('pyramid_persona', 'templates/forbidden.html').decode()
    html = template % {'js': request.persona_js, 'button': request.persona_button}
    return Response(html, status='403 Forbidden')
