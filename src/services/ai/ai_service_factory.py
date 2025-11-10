"""AI service factory for creating AI model instances."""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from ai import LanguageModel
from anthropic import Anthropic
from openai import OpenAI
from google.generativeai import GenerativeModel
import sys


@dataclass
class AIModelConfig:
    """AI model configuration."""
    provider: str
    model: str
    api_key: str


@dataclass
class AIServiceConfig:
    """AI service configuration."""
    main: Optional[AIModelConfig] = None
    research: Optional[AIModelConfig] = None
    fallback: Optional[AIModelConfig] = None
    prd: Optional[AIModelConfig] = None


class AIServiceFactory:
    """Factory for creating AI service instances."""
    
    _instance: Optional['AIServiceFactory'] = None
    _config: AIServiceConfig
    
    def __init__(self):
        """Initialize AI service factory."""
        if AIServiceFactory._instance is not None:
            raise RuntimeError("AIServiceFactory is a singleton. Use get_instance() instead.")
        self._config = self._build_configuration()
    
    @classmethod
    def get_instance(cls) -> 'AIServiceFactory':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.__init__()
        return cls._instance
    
    def _build_configuration(self) -> AIServiceConfig:
        """Build AI service configuration from environment variables."""
        from ...env import (
            AI_MAIN_MODEL,
            AI_RESEARCH_MODEL,
            AI_FALLBACK_MODEL,
            AI_PRD_MODEL
        )
        
        return AIServiceConfig(
            main=self._parse_model_config(AI_MAIN_MODEL),
            research=self._parse_model_config(AI_RESEARCH_MODEL),
            fallback=self._parse_model_config(AI_FALLBACK_MODEL),
            prd=self._parse_model_config(AI_PRD_MODEL)
        )
    
    def _parse_model_config(self, model_string: str) -> Optional[AIModelConfig]:
        """Parse model configuration from model string."""
        if not model_string:
            return None
        
        # Extract provider from model name
        provider: str
        model: str
        api_key: str
        
        if model_string.startswith('claude-'):
            provider = 'anthropic'
            model = model_string
            api_key = os.getenv('ANTHROPIC_API_KEY', '')
        elif model_string.startswith('gpt-') or model_string.startswith('o1'):
            provider = 'openai'
            model = model_string
            api_key = os.getenv('OPENAI_API_KEY', '')
        elif model_string.startswith('gemini-'):
            provider = 'google'
            model = model_string
            api_key = os.getenv('GOOGLE_API_KEY', '')
        elif 'perplexity' in model_string or 'llama' in model_string or 'sonar' in model_string:
            provider = 'perplexity'
            model = model_string
            api_key = os.getenv('PERPLEXITY_API_KEY', '')
        else:
            # Default to anthropic for unknown models
            provider = 'anthropic'
            model = 'claude-3-5-sonnet-20241022'
            api_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        if not api_key:
            sys.stderr.write(f"⚠️  AI Provider Warning: No API key found for {provider} provider. AI features using this provider will be disabled.\n")
            return None
        
        return AIModelConfig(provider=provider, model=model, api_key=api_key)
    
    def get_model(self, model_type: str) -> Optional[Any]:
        """Get AI model instance for specific use case."""
        config = getattr(self._config, model_type, None)
        
        if not config:
            sys.stderr.write(f"⚠️  AI Model Warning: {model_type} model is not available due to missing API key.\n")
            return None
        
        # For Python, we'll return the appropriate client/model
        # This is a simplified version - actual implementation would use proper AI SDKs
        if config.provider == 'anthropic':
            return Anthropic(api_key=config.api_key)
        elif config.provider == 'openai':
            return OpenAI(api_key=config.api_key)
        elif config.provider == 'google':
            return GenerativeModel(model_name=config.model)
        else:
            raise ValueError(f"Unsupported AI provider: {config.provider}")
    
    def get_main_model(self) -> Optional[Any]:
        """Get main AI model (for general task generation)."""
        return self.get_model('main')
    
    def get_research_model(self) -> Optional[Any]:
        """Get research AI model (for enhanced analysis)."""
        return self.get_model('research')
    
    def get_fallback_model(self) -> Optional[Any]:
        """Get fallback AI model (when main model fails)."""
        return self.get_model('fallback')
    
    def get_prd_model(self) -> Optional[Any]:
        """Get PRD AI model (for PRD generation)."""
        return self.get_model('prd')
    
    def get_best_available_model(self) -> Optional[Any]:
        """Get the best available model with fallback logic."""
        # Try main model first
        main_model = self.get_main_model()
        if main_model:
            return main_model
        
        # Try fallback model
        fallback_model = self.get_fallback_model()
        if fallback_model:
            return fallback_model
        
        # Try PRD model
        prd_model = self.get_prd_model()
        if prd_model:
            return prd_model
        
        # Try research model
        research_model = self.get_research_model()
        if research_model:
            return research_model
        
        # No models available
        return None
    
    def is_ai_available(self) -> bool:
        """Check if any AI functionality is available."""
        return self.get_best_available_model() is not None
    
    def get_configuration(self) -> AIServiceConfig:
        """Get configuration for debugging."""
        return self._config
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Check AI provider availability and configuration status."""
        missing: List[str] = []
        available: List[str] = []
        available_models: List[str] = []
        unavailable_models: List[str] = []
        
        # Check each provider
        if not os.getenv('ANTHROPIC_API_KEY'):
            missing.append('ANTHROPIC_API_KEY')
        else:
            available.append('anthropic')
        
        if not os.getenv('OPENAI_API_KEY'):
            missing.append('OPENAI_API_KEY')
        else:
            available.append('openai')
        
        if not os.getenv('GOOGLE_API_KEY'):
            missing.append('GOOGLE_API_KEY')
        else:
            available.append('google')
        
        if not os.getenv('PERPLEXITY_API_KEY'):
            missing.append('PERPLEXITY_API_KEY')
        else:
            available.append('perplexity')
        
        # Check which models are available
        if self._config.main:
            available_models.append('main')
        else:
            unavailable_models.append('main')
        
        if self._config.research:
            available_models.append('research')
        else:
            unavailable_models.append('research')
        
        if self._config.fallback:
            available_models.append('fallback')
        else:
            unavailable_models.append('fallback')
        
        if self._config.prd:
            available_models.append('prd')
        else:
            unavailable_models.append('prd')
        
        return {
            'has_any_provider': len(available) > 0,
            'available': available,
            'missing': missing,
            'available_models': available_models,
            'unavailable_models': unavailable_models
        }




