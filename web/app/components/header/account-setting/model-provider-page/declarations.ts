export type FormValue = Record<string, string>

export type TypeWithI18N<T = string> = {
  'en_US': T
  'zh_Hans': T
}

export enum FormTypeEnum {
  textInput = 'text-input',
  secretInput = 'secret-input',
  select = 'select',
  radio = 'radio',
}

export type FormOption = {
  label: TypeWithI18N
  value: string
}

export enum ModelTypeEnum {
  textGeneration = 'text-generation',
  textEmbedding = 'text-embedding',
  rerank = 'rerank',
  speech2text = 'speech2text',
  moderation = 'moderation',
}

export enum ConfigurateMethodEnum {
  predefinedModel = 'predefined-model',
  customizableModel = 'customizable-model',
  fetchFromRemote = 'fetch-from-remote',
}

export enum ModelFeature {
  toolCall = 'tool-call',
  multiToolCall = 'multi-tool-call',
  agentThought = 'agent_thought',
  vision = 'vision',
}

export enum ModelStatus {
  active = 'active',
  noConfigure = 'no-configure',
  quotaExceeded = 'quota-exceeded',
  noPermission = 'no-permission',
}

export type FormShowOnObject = {
  variable: string
  value: string
}

export type CredentialFormSchemaMap = {
  [FormTypeEnum.textInput]: { max_length: number; placeholder: TypeWithI18N }
  [FormTypeEnum.select]: { options: FormOption[] }
  [FormTypeEnum.radio]: { options: FormOption[] }
  [FormTypeEnum.secretInput]: { placeholder: TypeWithI18N }
}

export type CredentialFormSchemaBase = {
  variable: string
  label: TypeWithI18N
  type: FormTypeEnum
  required: boolean
  default: string
  show_on: FormShowOnObject[]
}

export type CredentialFormSchemaTextInput = CredentialFormSchemaBase & { max_length: number; placeholder: TypeWithI18N }
export type CredentialFormSchemaSelect = CredentialFormSchemaBase & { options: FormOption[] }
export type CredentialFormSchemaRadio = CredentialFormSchemaBase & { options: FormOption[] }
export type CredentialFormSchemaSecretInput = CredentialFormSchemaBase & { placeholder: TypeWithI18N }
export type CredentialFormSchema = CredentialFormSchemaTextInput | CredentialFormSchemaSelect | CredentialFormSchemaRadio | CredentialFormSchemaSecretInput

export type Model = {
  model: string
  label: TypeWithI18N
  model_type: ModelTypeEnum
  features: ModelFeature[]
  configurate_method: ConfigurateMethodEnum
  status: ModelStatus
}

export enum PreferredProviderTypeEnum {
  system = 'system',
  custom = 'custom',
}

export enum CurrentSystemQuotaTypeEnum {
  trial = 'trial',
  free = 'free',
  paid = 'paid',
}

export enum QuotaUnitEnum {
  times = 'times',
  tokens = 'tokens',
}

export type QuotaConfiguration = {
  quota_type: CurrentSystemQuotaTypeEnum
  quota_unit: QuotaUnitEnum
  quota_limit: number
  quota_used: number
  last_used: number
  is_valid: boolean
}

export type ModelProvider = {
  provider: string
  label: TypeWithI18N
  description?: TypeWithI18N
  help_url: TypeWithI18N
  help_text: TypeWithI18N
  icon_small: TypeWithI18N
  icon_large: TypeWithI18N
  background?: string
  supported_models_types: ModelTypeEnum[]
  configurate_methods: ConfigurateMethodEnum[]
  provider_credential_schema: {
    credential_form_schemas: CredentialFormSchema[]
  }
  model_credential_schema: {
    model: {
      label: TypeWithI18N
      placeholder: TypeWithI18N
    }
    crenential_form_schemas: CredentialFormSchema[]
  }
  preferred_provider_type: PreferredProviderTypeEnum
  custom_configuration: {
    status: 'active' | 'no_configure'
  }
  system_configuration: {
    enabled: boolean
    current_system_quota_type: CurrentSystemQuotaTypeEnum
    quota_configurations: QuotaConfiguration[]
  }
}
