import json
import re
from config import Config


class AIService:
    """Service for interacting with multiple AI providers for test case generation."""
    
    # Available providers with free tiers
    PROVIDERS = {
        'openrouter': {
            'name': 'OpenRouter (DeepSeek)',
            'description': 'Free: DeepSeek model',
            'requires': 'OPENROUTER_API_KEY'
        },
        'gemini': {
            'name': 'Google Gemini',
            'description': 'Free: 1,500 requests/day',
            'requires': 'GOOGLE_API_KEY'
        },
        'groq': {
            'name': 'Groq (Llama 3.1)',
            'description': 'Free: 14,400 requests/day',
            'requires': 'GROQ_API_KEY'
        },
        'together': {
            'name': 'Together AI',
            'description': 'Free: $1 credit on signup',
            'requires': 'TOGETHER_API_KEY'
        },
        'anthropic': {
            'name': 'Anthropic Claude',
            'description': 'Paid: Pay per token',
            'requires': 'ANTHROPIC_API_KEY'
        },
        'mock': {
            'name': 'Demo Mode',
            'description': 'No API key required',
            'requires': None
        }
    }
    
    def __init__(self):
        self.gemini_client = None
        self.groq_client = None
        self.anthropic_client = None
        
        # Initialize available clients
        if Config.GOOGLE_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=Config.GOOGLE_API_KEY)
                self.gemini_client = genai.GenerativeModel(Config.GEMINI_MODEL)
            except Exception as e:
                print(f"Gemini init error: {e}")
        
        if Config.GROQ_API_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
            except Exception as e:
                print(f"Groq init error: {e}")
        
        if Config.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            except Exception as e:
                print(f"Anthropic init error: {e}")
    
    def get_available_providers(self) -> list:
        """Get list of available providers based on configured API keys."""
        available = []
        
        # OpenRouter first (recommended free option)
        if Config.OPENROUTER_API_KEY:
            available.append({
                'id': 'openrouter',
                **self.PROVIDERS['openrouter']
            })
        
        if Config.GOOGLE_API_KEY:
            available.append({
                'id': 'gemini',
                **self.PROVIDERS['gemini']
            })
        
        if Config.GROQ_API_KEY:
            available.append({
                'id': 'groq',
                **self.PROVIDERS['groq']
            })
        
        if Config.TOGETHER_API_KEY:
            available.append({
                'id': 'together',
                **self.PROVIDERS['together']
            })
        
        if Config.ANTHROPIC_API_KEY:
            available.append({
                'id': 'anthropic',
                **self.PROVIDERS['anthropic']
            })
        
        # Always add mock/demo mode
        available.append({
            'id': 'mock',
            **self.PROVIDERS['mock']
        })
        
        return available
    
    def generate_test_cases(self, requirements: str, project_type: str, provider: str = None) -> dict:
        """
        Generate test cases from requirements using specified AI provider.
        
        Args:
            requirements: The software requirements text
            project_type: Type of project (Web, Mobile, API, Desktop)
            provider: AI provider to use (gemini, groq, together, anthropic, mock)
            
        Returns:
            Dictionary containing test cases data
        """
        # Use default provider if not specified
        if not provider:
            provider = Config.DEFAULT_AI_PROVIDER
        
        prompt = self._build_prompt(requirements, project_type)
        
        try:
            if provider == 'openrouter' and Config.OPENROUTER_API_KEY:
                return self._generate_with_openrouter(prompt)
            elif provider == 'gemini' and self.gemini_client:
                return self._generate_with_gemini(prompt)
            elif provider == 'groq' and self.groq_client:
                return self._generate_with_groq(prompt)
            elif provider == 'together' and Config.TOGETHER_API_KEY:
                return self._generate_with_together(prompt)
            elif provider == 'anthropic' and self.anthropic_client:
                return self._generate_with_anthropic(prompt)
            else:
                return self._generate_mock_test_cases(requirements, project_type)
        except Exception as e:
            print(f"AI generation error ({provider}): {str(e)}")
            # Fallback to mock on error
            result = self._generate_mock_test_cases(requirements, project_type)
            result['error'] = f"AI provider error: {str(e)}"
            return result
    
    def _build_prompt(self, requirements: str, project_type: str) -> str:
        """Build the prompt for AI providers."""
        return f"""You are an expert QA engineer. Generate industry-standard test cases based on the following requirements.

Project Type: {project_type}

Requirements:
{requirements}

Generate comprehensive test cases in JSON format. Each test case should include:
- Test ID (format: TC_XXX)
- Module (the feature/component being tested)
- Test Scenario (description of what is being tested)
- Preconditions (what must be true before the test)
- Steps (numbered list of test steps)
- Test Data (sample data to use)
- Expected Result (what should happen)
- Actual Result (leave as empty string)
- Status (leave as "Pending")
- Priority (High, Medium, or Low)
- Severity (Critical, Major, Minor, or Trivial)
- Edge Cases (any edge case considerations)

Return the response as a valid JSON object with this structure:
{{
    "test_cases": [
        {{
            "test_id": "TC_001",
            "module": "...",
            "test_scenario": "...",
            "preconditions": "...",
            "steps": "1. Step one\\n2. Step two\\n3. Step three",
            "test_data": "...",
            "expected_result": "...",
            "actual_result": "",
            "status": "Pending",
            "priority": "High|Medium|Low",
            "severity": "Critical|Major|Minor|Trivial",
            "edge_cases": "..."
        }}
    ],
    "summary": {{
        "total_test_cases": X,
        "high_priority": X,
        "medium_priority": X,
        "low_priority": X
    }}
}}

Generate at least 5-10 comprehensive test cases covering positive, negative, and edge cases.
IMPORTANT: Return ONLY the JSON object, no additional text or markdown formatting."""
    
    def _generate_with_openrouter(self, prompt: str) -> dict:
        """Generate test cases using OpenRouter (DeepSeek free model)."""
        import openai
        
        client = openai.OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        
        response = client.chat.completions.create(
            model=Config.OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096
        )
        return self._parse_response(response.choices[0].message.content, 'openrouter')
    
    def _generate_with_gemini(self, prompt: str) -> dict:
        """Generate test cases using Google Gemini."""
        response = self.gemini_client.generate_content(prompt)
        return self._parse_response(response.text, 'gemini')
    
    def _generate_with_groq(self, prompt: str) -> dict:
        """Generate test cases using Groq."""
        chat_completion = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=Config.GROQ_MODEL,
            temperature=0.7,
            max_tokens=4096
        )
        return self._parse_response(chat_completion.choices[0].message.content, 'groq')
    
    def _generate_with_together(self, prompt: str) -> dict:
        """Generate test cases using Together AI."""
        import openai
        
        client = openai.OpenAI(
            api_key=Config.TOGETHER_API_KEY,
            base_url="https://api.together.xyz/v1"
        )
        
        response = client.chat.completions.create(
            model=Config.TOGETHER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096
        )
        return self._parse_response(response.choices[0].message.content, 'together')
    
    def _generate_with_anthropic(self, prompt: str) -> dict:
        """Generate test cases using Anthropic Claude."""
        message = self.anthropic_client.messages.create(
            model=Config.AI_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return self._parse_response(message.content[0].text, 'anthropic')
    
    def _parse_response(self, response_text: str, provider: str) -> dict:
        """Parse the AI response into structured data."""
        try:
            # Try to extract JSON from the response
            cleaned = response_text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            result['provider'] = provider
            return result
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    result['provider'] = provider
                    return result
                except json.JSONDecodeError:
                    pass
            
            # Return a structured error response
            return {
                "test_cases": [],
                "error": "Failed to parse AI response",
                "provider": provider,
                "raw_response": response_text[:500]
            }
    
    def _generate_mock_test_cases(self, requirements: str, project_type: str) -> dict:
        """Generate mock test cases when no API is available."""
        words = requirements.split()[:10]
        module_name = words[0] if words else "Feature"
        
        mock_test_cases = [
            {
                "test_id": "TC_001",
                "module": f"{module_name} - Core Functionality",
                "test_scenario": "Verify basic functionality works as expected",
                "preconditions": "System is accessible and user is authenticated",
                "steps": "1. Navigate to the feature\n2. Perform the primary action\n3. Verify the result",
                "test_data": "Valid input data",
                "expected_result": "Action completes successfully with expected output",
                "actual_result": "",
                "status": "Pending",
                "priority": "High",
                "severity": "Critical",
                "edge_cases": "Test with minimum and maximum valid inputs"
            },
            {
                "test_id": "TC_002",
                "module": f"{module_name} - Input Validation",
                "test_scenario": "Verify system handles invalid input gracefully",
                "preconditions": "System is accessible",
                "steps": "1. Navigate to the input form\n2. Enter invalid data\n3. Submit the form\n4. Verify error handling",
                "test_data": "Invalid/malformed input data",
                "expected_result": "System displays appropriate error message",
                "actual_result": "",
                "status": "Pending",
                "priority": "High",
                "severity": "Major",
                "edge_cases": "Test with empty inputs, special characters, SQL injection attempts"
            },
            {
                "test_id": "TC_003",
                "module": f"{module_name} - Boundary Testing",
                "test_scenario": "Verify system handles boundary conditions",
                "preconditions": "System is accessible with valid permissions",
                "steps": "1. Test with minimum boundary value\n2. Test with maximum boundary value\n3. Test with values just outside boundaries",
                "test_data": "Boundary values (min, max, min-1, max+1)",
                "expected_result": "System accepts valid boundary values and rejects invalid ones",
                "actual_result": "",
                "status": "Pending",
                "priority": "Medium",
                "severity": "Major",
                "edge_cases": "Consider integer overflow, date boundaries"
            },
            {
                "test_id": "TC_004",
                "module": f"{module_name} - Error Handling",
                "test_scenario": "Verify system error handling and recovery",
                "preconditions": "System is accessible",
                "steps": "1. Simulate error condition\n2. Verify error is logged\n3. Verify user-friendly message displayed\n4. Verify system recovery",
                "test_data": "Conditions that trigger errors",
                "expected_result": "System handles errors gracefully without crashing",
                "actual_result": "",
                "status": "Pending",
                "priority": "Medium",
                "severity": "Major",
                "edge_cases": "Network failures, timeout conditions, server errors"
            },
            {
                "test_id": "TC_005",
                "module": f"{module_name} - {project_type} Specific",
                "test_scenario": f"Verify {project_type}-specific requirements",
                "preconditions": f"{project_type} environment is properly configured",
                "steps": f"1. Set up {project_type} test environment\n2. Execute {project_type}-specific test\n3. Verify results",
                "test_data": f"{project_type}-specific test data",
                "expected_result": f"All {project_type}-specific requirements are met",
                "actual_result": "",
                "status": "Pending",
                "priority": "High",
                "severity": "Critical",
                "edge_cases": f"Cross-platform compatibility for {project_type}"
            }
        ]
        
        return {
            "test_cases": mock_test_cases,
            "summary": {
                "total_test_cases": len(mock_test_cases),
                "high_priority": 3,
                "medium_priority": 2,
                "low_priority": 0
            },
            "provider": "mock",
            "note": "Demo mode - Configure an AI provider API key for real test case generation"
        }
