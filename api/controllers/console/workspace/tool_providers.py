import json

from flask_login import current_user
from libs.login import login_required
from flask_restful import Resource, abort, reqparse
from werkzeug.exceptions import Forbidden

from controllers.console import api
from controllers.console.setup import setup_required
from controllers.console.wraps import account_initialization_required

from services.tools_manage_service import ToolManageService

class ToolProviderListApi(Resource):

    @setup_required
    @login_required
    @account_initialization_required
    def get(self):
        user_id = current_user.id
        tenant_id = current_user.current_tenant_id

        return ToolManageService.list_tool_providers(user_id, tenant_id)

class ToolBuiltinProviderAddApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self, provider):
        user_id = current_user.id
        tenant_id = current_user.current_tenant_id

        parser = reqparse.RequestParser()
        parser.add_argument('credentials', type=dict, required=True, nullable=False, location='json')

        args = parser.parse_args()

        return ToolManageService.create_builtin_tool_provider(
            user_id,
            tenant_id,
            provider,
            args['credentials'],
        )

class ToolBuiltinProviderDeleteApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self, provider):
        user_id = current_user.id
        tenant_id = current_user.current_tenant_id

        return ToolManageService.delete_builtin_tool_provider(
            user_id,
            tenant_id,
            provider,
        )
    
class ToolBuiltinProviderUpdateApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self, provider):
        user_id = current_user.id
        tenant_id = current_user.current_tenant_id

        parser = reqparse.RequestParser()
        parser.add_argument('credentials', type=dict, required=True, nullable=False, location='json')

        args = parser.parse_args()

        return ToolManageService.update_builtin_tool_provider(
            user_id,
            tenant_id,
            provider,
            args['credentials'],
        )

class ToolApiProviderAddApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self):
        user_id = current_user.id
        tenant_id = current_user.current_tenant_id

        parser = reqparse.RequestParser()
        parser.add_argument('credentials', type=dict, required=True, nullable=False, location='json')
        parser.add_argument('parameters', type=dict, required=True, nullable=False, location='json')
        parser.add_argument('schema_type', type=str, required=True, nullable=False, location='json')
        parser.add_argument('schema', type=str, required=True, nullable=False, location='json')
        parser.add_argument('provider', type=str, required=True, nullable=False, location='json')
        parser.add_argument('icon', type=str, required=True, nullable=False, location='json')
        parser.add_argument('description', type=str, required=True, nullable=False, location='json')

        args = parser.parse_args()

        return ToolManageService.create_api_tool_provider(
            user_id,
            tenant_id,
            args['provider'],
            args['icon'],
            args['description'],
            args['credentials'],
            args['parameters'],
            args['schema_type'],
            args['schema'],
        )

class ToolApiProviderUpdateApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self):
        user_id = current_user.id
        tenant_id = current_user.current_tenant_id

        parser = reqparse.RequestParser()
        parser.add_argument('credentials', type=dict, required=True, nullable=False, location='json')
        parser.add_argument('parameters', type=dict, required=True, nullable=False, location='json')
        parser.add_argument('schema_type', type=str, required=True, nullable=False, location='json')
        parser.add_argument('schema', type=str, required=True, nullable=False, location='json')
        parser.add_argument('provider', type=str, required=True, nullable=False, location='json')
        parser.add_argument('icon', type=str, required=True, nullable=False, location='json')
        parser.add_argument('description', type=str, required=True, nullable=False, location='json')

        args = parser.parse_args()

        return ToolManageService.update_api_tool_provider(
            user_id,
            tenant_id,
            args['provider'],
            args['icon'],
            args['description'],
            args['credentials'],
            args['parameters'],
            args['schema_type'],
            args['schema'],
        )

class ToolApiProviderDeleteApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self):
        user_id = current_user.id
        tenant_id = current_user.current_tenant_id

        parser = reqparse.RequestParser()

        parser.add_argument('provider', type=str, required=True, nullable=False, location='json')

        args = parser.parse_args()

        return ToolManageService.delete_api_tool_provider(
            user_id,
            tenant_id,
            args['provider'],
        )

class ToolBuiltinProviderCredentialsSchemaApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self, provider):
        return ToolManageService.list_builtin_provider_credentials_schema(provider)

class ToolApiProviderSchemaApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('schema_type', type=str, required=True, nullable=False, location='json')
        parser.add_argument('schema', type=str, required=True, nullable=False, location='json')

        args = parser.parse_args()

        return ToolManageService.parser_api_schema(
            schema_type=args['schema_type'],
            schema=args['schema'],
        )

# new apis
api.add_resource(ToolProviderListApi, '/workspaces/current/tool-providers')
api.add_resource(ToolBuiltinProviderAddApi, '/workspaces/current/tool-provider/builtin/<provider>/add')
api.add_resource(ToolBuiltinProviderDeleteApi, '/workspaces/current/tool-provider/builtin/<provider>/delete')
api.add_resource(ToolBuiltinProviderUpdateApi, '/workspaces/current/tool-provider/builtin/<provider>/update')
api.add_resource(ToolBuiltinProviderCredentialsSchemaApi, '/workspaces/current/tool-provider/builtin/<provider>/credentials_schema')
api.add_resource(ToolApiProviderAddApi, '/workspaces/current/tool-provider/api/add')
api.add_resource(ToolApiProviderUpdateApi, '/workspaces/current/tool-provider/api/update')
api.add_resource(ToolApiProviderDeleteApi, '/workspaces/current/tool-provider/api/delete')
api.add_resource(ToolApiProviderSchemaApi, '/workspaces/current/tool-provider/api/schema')