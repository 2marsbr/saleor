import json

import graphene
from django.shortcuts import reverse
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE
from tests.utils import get_graphql_content

from saleor.core.permissions import MODELS_PERMISSIONS
from saleor.graphql.core.utils import clean_seo_fields, snake_to_camel_case


def test_shop_endpoint(settings, admin_api_client):
    query = """
    query shop {
        shop {
            permissions {
                code
                name
            }
            languages {
                code
                language
            }
            phonePrefixes
        }
    }
    """
    languages = settings.LANGUAGES
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)

    assert 'errors' not in content
    data = content['data']['shop']
    permissions = data['permissions']
    permissions_codes = {permission.get('code') for permission in permissions}
    assert len(permissions_codes) == len(MODELS_PERMISSIONS)
    for code in permissions_codes:
        assert code in MODELS_PERMISSIONS
    assert len(data['languages']) == len(languages)
    assert len(data['phonePrefixes']) == len(COUNTRY_CODE_TO_REGION_CODE)


def test_clean_seo_fields():
    title = 'lady title'
    description = 'fantasy description'
    data = {'seo':
                {'title': title,
                 'description': description}}
    clean_seo_fields(data)
    assert data['seo_title'] == title
    assert data['seo_description'] == description


def test_snake_to_camel_case():
    assert snake_to_camel_case('test_camel_case') == 'testCamelCase'
    assert snake_to_camel_case('testCamel_case') == 'testCamelCase'
    assert snake_to_camel_case(123) == 123


def test_mutation_returns_error_field_in_camel_case(admin_api_client, variant):
    # costPrice is snake case variable (cost_price) in the backend
    query = """
    mutation testCamel($id: ID!, $cost: Decimal) {
        productVariantUpdate(id: $id,
        input: {costPrice: $cost, trackInventory: false}) {
            errors {
                field
                message
            }
            productVariant {
                id
            }
        }
    }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('ProductVariant', variant.id),
        'cost': '12.1234'})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    error = content['data']['productVariantUpdate']['errors'][0]
    assert error['field'] == 'costPrice'


def test_user_error_field_name_for_related_object(admin_api_client):
    query = """
    mutation {
        categoryCreate(input: {name: "Test", parent: "123456"}) {
            errors {
                field
                message
            }
            category {
                id
            }
        }
    }
    """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    data = content['data']['categoryCreate']['category']
    assert data is None
    error = content['data']['categoryCreate']['errors'][0]
    assert error['field'] == 'parent'
