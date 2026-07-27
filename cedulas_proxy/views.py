import requests
from django.http import JsonResponse
from django.core.cache import cache


class CedulaLookupError(Exception):
    pass


def get_cedula_data(query):
    cache_key = f'cedula_{query}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        response = requests.get(
            f'https://apis.gometa.org/cedulas/{query}',
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise CedulaLookupError('No fue posible consultar la cédula en este momento.') from exc
    cache.set(cache_key, data, timeout=60 * 60 * 24 * 7)
    return data


def cedula_proxy(request, query):
    try:
        data = get_cedula_data(query)
        return JsonResponse(data, safe=not isinstance(data, list))
    except CedulaLookupError:
        return JsonResponse({'error': 'No fue posible consultar la cédula en este momento.'}, status=503)
