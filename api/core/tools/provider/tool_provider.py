from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from pydantic import BaseModel
from os import path, listdir
from yaml import load, FullLoader

from core.model_runtime.entities.message_entities import PromptMessage
from core.tools.entities.tool_entities import AssistantAppMessage, ToolProviderType, \
    ToolProviderIdentity, ToolParamter, ToolProviderCredentials
from core.tools.provider.tool import Tool
from core.tools.entities.user_entities import UserToolProviderCredentials
from core.tools.errors import ToolNotFoundError, ToolProviderNotFoundError, \
    ToolParamterValidationError, ToolProviderCredentialValidationError

import importlib

class ToolProvider(BaseModel, ABC):
    identity: Optional[ToolProviderIdentity] = None
    tools: Optional[List[Tool]] = None
    credentials_schema: Optional[Dict[str, ToolProviderCredentials]] = None

    def __init__(self):
        if self.app_type == ToolProviderType.API_BASED or self.app_type == ToolProviderType.APP_BASED:
            super().__init__()
            return
        
        # load provider yaml
        provider = self.__class__.__module__.split('.')[-1]
        yaml_path = path.join(path.dirname(path.realpath(__file__)), 'builtin', provider, f'{provider}.yaml')
        try:
            with open(yaml_path, 'r') as f:
                provider_yaml = load(f.read(), FullLoader)
        except:
            raise ToolProviderNotFoundError(f'can not load provider yaml for {provider}')

        if 'credentails_for_provider' in provider_yaml:
            # set credentials name
            for credential_name in provider_yaml['credentails_for_provider']:
                provider_yaml['credentails_for_provider'][credential_name]['name'] = credential_name

        super().__init__(**{
            'identity': provider_yaml['identity'],
            'credentials_schema': provider_yaml['credentails_for_provider'] if 'credentails_for_provider' in provider_yaml else None,
        })

    def _get_bulitin_tools(self) -> List[Tool]:
        """
            returns a list of tools that the provider can provide

            :return: list of tools
        """
        if self.tools:
            return self.tools
        
        provider = self.identity.name
        tool_path = path.join(path.dirname(path.realpath(__file__)), "builtin", provider, "tools")
        # get all the yaml files in the tool path
        tool_files = list(filter(lambda x: x.endswith(".yaml") and not x.startswith("__"), listdir(tool_path)))
        tools = []
        for tool_file in tool_files:
            with open(path.join(tool_path, tool_file), "r") as f:
                # get tool name
                tool_name = tool_file.split(".")[0]
                tool = load(f.read(), FullLoader)
                # get tool class, import the module
                py_path = path.join(path.dirname(path.realpath(__file__)), 'builtin', provider, 'tools', f'{tool_name}.py')
                spec = importlib.util.spec_from_file_location(f'core.tools.provider.builtin.{provider}.tools.{tool_name}', py_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                # get all the classes in the module
                classes = [x for _, x in vars(mod).items() if isinstance(x, type) and x != Tool and issubclass(x, Tool)]
                assistant_tool_class = classes[0]
                tools.append(assistant_tool_class(**tool))

        self.tools = tools
        return tools
    
    def get_credentails_schema(self) -> Dict[str, ToolProviderCredentials]:
        """
            returns the credentials schema of the provider

            :return: the credentials schema
        """
        return self.credentials_schema.copy()
    
    def user_get_credentails_schema(self) -> UserToolProviderCredentials:
        """
            returns the credentials schema of the provider, this method is used for user

            :return: the credentials schema
        """
        credentials = self.credentials_schema.copy()
        return UserToolProviderCredentials(credentails=credentials)

    def get_tools(self) -> List[Tool]:
        """
            returns a list of tools that the provider can provide

            :return: list of tools
        """
        if self.app_type == ToolProviderType.BUILT_IN:
            return self._get_bulitin_tools()
        
        # app based or api based will override this method
        raise NotImplementedError('get_tools should be implemented by the subclass')

    def get_parameters(self, tool_name: str) -> List[ToolParamter]:
        """
            returns the parameters of the tool

            :param tool_name: the name of the tool, defined in `get_tools`
            :return: list of parameters
        """
        tool = next(filter(lambda x: x.identity.name == tool_name, self.get_tools()), None)
        if tool is None:
            raise ToolNotFoundError(f'tool {tool_name} not found')
        return tool.parameters

    @property
    def app_type(self) -> ToolProviderType:
        """
            returns the type of the provider

            :return: type of the provider
        """
        return ToolProviderType.BUILT_IN

    def _invoke(
        self,
        tool_name: str,
        tool_paramters: Dict[str, Any],
        credentials: Dict[str, Any],
        prompt_messages: List[PromptMessage],
    ) -> List[AssistantAppMessage]:
        """
            should be implemented by the subclass

            tool_name: the name of the tool, defined in `get_tools`
            tool_paramters: the parameters of the tool
            credentials: the credentials of the tool
            prompt_messages: the prompt messages that the tool can use

            :return: the messages that the tool wants to send to the user
        """
        # get tool
        tool = next(filter(lambda x: x.identity.name == tool_name, self.get_tools()), None)
        if tool is None:
            raise ToolNotFoundError(f'tool {tool_name} not found')
        
        # invoke
        return tool.invoke(tool_paramters, credentials, prompt_messages)

    def invoke(
        self,
        tool_id: int,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        credentials: Dict[str, Any],
        prompt_messages: List[PromptMessage],
    ) -> List[AssistantAppMessage]:
        """
            invoke will detect which type of assistant should be used and route the request to the correct method
        
            tool_name: the name of the tool, defined in `get_tools`
            tool_paramters: the parameters of the tool
            credentials: the credentials of the tool
            prompt_messages: the prompt messages that the tool can use

            :return: the messages that the tool wants to send to the user
        """
        # validate parameters
        self.validate_parameters(tool_id=tool_id, tool_name=tool_name, tool_parameters=tool_parameters)

        if self.app_type == ToolProviderType.APP_BASED:
            # use app based assistant
            return self.invoke_app_based(tool_id, tool_name, tool_parameters, credentials, prompt_messages)
        elif self.app_type == ToolProviderType.API_BASED:
            # use api based assistant
            return self.invoke_api_based(tool_id, tool_name, tool_parameters, credentials, prompt_messages)
        else:
            # use built-in assistant, _invoke should be implemented by the subclass
            return self._invoke(tool_name, tool_parameters, credentials, prompt_messages)

    def invoke_app_based(
        self,
        tool_id: int,
        tool_name: str,
        tool_paramters: Dict[str, Any],
        credentials: Dict[str, Any],
        prompt_messages: List[PromptMessage],
    ) -> List[AssistantAppMessage]:
        """
            invoke app based assistant

            tool_name: the name of the tool, defined in `get_tools`
            tool_paramters: the parameters of the tool
            credentials: the credentials of the tool
            prompt_messages: the prompt messages that the tool can use

            :return: the messages that the tool wants to send to the user
        """
        raise NotImplementedError()

    def invoke_api_based(
        self,
        tool_id: int,
        tool_name: str,
        tool_paramters: Dict[str, Any],
        credentials: Dict[str, Any],
        prompt_messages: List[PromptMessage],
    ) -> List[AssistantAppMessage]:
        """
            invoke api based assistant

            tool_name: the name of the tool, defined in `get_tools`
            tool_paramters: the parameters of the tool
            credentials: the credentials of the tool
            prompt_messages: the prompt messages that the tool can use

            :return: the messages that the tool wants to send to the user
        """
        raise NotImplementedError()

    def validate_parameters(self, tool_id: int, tool_name: str, tool_parameters: Dict[str, Any]) -> None:
        """
            validate the parameters of the tool and set the default value if needed

            :param tool_name: the name of the tool, defined in `get_tools`
            :param tool_parameters: the parameters of the tool
        """
        tool_parameters_schema = self.get_parameters(tool_name)
        
        tool_parameters_need_to_validate: Dict[str, ToolParamter] = {}
        for parameter in tool_parameters_schema:
            tool_parameters_need_to_validate[parameter.name] = parameter

        for parameter in tool_parameters:
            if parameter not in tool_parameters_need_to_validate:
                raise ToolParamterValidationError(f'parameter {parameter} not found in tool {tool_name}')
            
            # check type
            parameter_schema = tool_parameters_need_to_validate[parameter]
            if parameter_schema.type == ToolParamter.ToolParameterType.STRING:
                if not isinstance(tool_parameters[parameter], str):
                    raise ToolParamterValidationError(f'parameter {parameter} should be string')
            
            elif parameter_schema.type == ToolParamter.ToolParameterType.NUMBER:
                if not isinstance(tool_parameters[parameter], (int, float)):
                    raise ToolParamterValidationError(f'parameter {parameter} should be number')
                
                if parameter_schema.min is not None and tool_parameters[parameter] < parameter_schema.min:
                    raise ToolParamterValidationError(f'parameter {parameter} should be greater than {parameter_schema.min}')
                
                if parameter_schema.max is not None and tool_parameters[parameter] > parameter_schema.max:
                    raise ToolParamterValidationError(f'parameter {parameter} should be less than {parameter_schema.max}')
                
            elif parameter_schema.type == ToolParamter.ToolParameterType.BOOLEAN:
                if not isinstance(tool_parameters[parameter], bool):
                    raise ToolParamterValidationError(f'parameter {parameter} should be boolean')
                
            elif parameter_schema.type == ToolParamter.ToolParameterType.SELECT:
                if not isinstance(tool_parameters[parameter], str):
                    raise ToolParamterValidationError(f'parameter {parameter} should be string')
                
                options = parameter_schema.options
                if not isinstance(options, list):
                    raise ToolParamterValidationError(f'parameter {parameter} options should be list')
                
                if tool_parameters[parameter] not in [x.value for x in options]:
                    raise ToolParamterValidationError(f'parameter {parameter} should be one of {options}')
                
            tool_parameters_need_to_validate.pop(parameter)

        for parameter in tool_parameters_need_to_validate:
            parameter_schema = tool_parameters_need_to_validate[parameter]
            if parameter_schema.required:
                raise ToolParamterValidationError(f'parameter {parameter} is required')
            
            # the parameter is not set currently, set the default value if needed
            if parameter_schema.default is not None:
                default_value = parameter_schema.default
                # parse default value into the correct type
                if parameter_schema.type == ToolParamter.ToolParameterType.STRING or \
                    parameter_schema.type == ToolParamter.ToolParameterType.SELECT:
                    default_value = str(default_value)
                elif parameter_schema.type == ToolParamter.ToolParameterType.NUMBER:
                    default_value = float(default_value)
                elif parameter_schema.type == ToolParamter.ToolParameterType.BOOLEAN:
                    default_value = bool(default_value)

                tool_parameters[parameter] = default_value

    def validate_credentials_format(self, credentials: Dict[str, Any]) -> None:
        """
            validate the format of the credentials of the provider and set the default value if needed

            :param credentials: the credentials of the tool
        """
        credentials_schema = self.credentials_schema
        if credentials_schema is None:
            return
        
        credentials_need_to_validate: Dict[str, ToolProviderCredentials] = {}
        for credential_name in credentials_schema:
            credentials_need_to_validate[credential_name] = credentials_schema[credential_name]

        for credential_name in credentials:
            if credential_name not in credentials_need_to_validate:
                raise ToolProviderCredentialValidationError(f'credential {credential_name} not found in provider {self.identity.name}')
            
            # check type
            credential_schema = credentials_need_to_validate[credential_name]
            if credential_schema == ToolProviderCredentials.CredentialsType.SECRET_INPUT or \
                credential_schema == ToolProviderCredentials.CredentialsType.TEXT_INPUT:
                if not isinstance(credentials[credential_name], str):
                    raise ToolProviderCredentialValidationError(f'credential {credential_name} should be string')
            
            elif credential_schema.type == ToolProviderCredentials.CredentialsType.SELECT:
                if not isinstance(credentials[credential_name], str):
                    raise ToolProviderCredentialValidationError(f'credential {credential_name} should be string')
                
                options = credential_schema.options
                if not isinstance(options, list):
                    raise ToolProviderCredentialValidationError(f'credential {credential_name} options should be list')
                
                if credentials[credential_name] not in [x.value for x in options]:
                    raise ToolProviderCredentialValidationError(f'credential {credential_name} should be one of {options}')
                
            credentials_need_to_validate.pop(credential_name)

        for credential_name in credentials_need_to_validate:
            credential_schema = credentials_need_to_validate[credential_name]
            if credential_schema.required:
                raise ToolProviderCredentialValidationError(f'credential {credential_name} is required')
            
            # the credential is not set currently, set the default value if needed
            if credential_schema.default is not None:
                default_value = credential_schema.default
                # parse default value into the correct type
                if credential_schema.type == ToolProviderCredentials.CredentialsType.SECRET_INPUT or \
                    credential_schema.type == ToolProviderCredentials.CredentialsType.TEXT_INPUT or \
                    credential_schema.type == ToolProviderCredentials.CredentialsType.SELECT:
                    default_value = str(default_value)

                credentials[credential_name] = default_value

    def validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
            validate the credentials of the provider

            :param tool_name: the name of the tool, defined in `get_tools`
            :param credentials: the credentials of the tool
        """
        # validate credentials format
        self.validate_credentials_format(credentials)

        # validate credentials
        self._validate_credentials(credentials)

    @abstractmethod
    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
            validate the credentials of the provider

            :param tool_name: the name of the tool, defined in `get_tools`
            :param credentials: the credentials of the tool
        """
        pass