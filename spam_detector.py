import re
from urllib.parse import urlparse
import json

class SpamDetector:
    def __init__(self):
        # Common spam phrases and patterns
        self.spam_patterns = [
            # Money and Prize patterns
            r'\b(?:free|win|won)\s+(?:money|prize|cash|gift)\b',
            r'\b(?:earn|make)\s+money\b',
            r'\bget\s+rich\b',
            r'\bdouble\s+your\b',
            r'\b100%\s+free\b',
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?(?:/(?:month|week|day))?\b',
            r'\b\d+k?\s*(?:USD|EUR|GBP)\b',
            
            # Urgency patterns
            r'\b(?:limited|special)(?:\s+\w+){0,2}\s+(?:offer|time|deal)\b',
            r'\b(?:urgent|emergency|immediate)\b',
            r'\b(?:expires?|ending)\s+(?:soon|today|now)\b',
            r'\b(?:last|final)\s+(?:chance|call|opportunity)\b',
            r'\b(?:hurry|rush|quick)\b',
            r'\b(?:now|today|tonight)\s+only\b',
            r'\btime\s+(?:running|running out|limited)\b',
            r'\b(?:act|click|call|buy|sign[- ]?up)\s+(?:now|today|immediately)\b',
            r'\bclaim\s+(?:now|today|your)\b',
            r'\bdon\'t\s+(?:miss|wait|delay)\b',
            r'\b(?:spots?|spaces?|seats?)\s+(?:limited|remaining)\b',
            
            # Financial patterns
            r'\b(?:credit|loan)\s+(?:card|approved|guaranteed|instant)\b',
            r'\b(?:investment|business)\s+opportunity\b',
            r'\b(?:save|discount|off|sale)\s+(?:\d+%|up to)\b',
            r'\bno\s+(?:credit\s+check|hidden\s+fees)\b',
            r'\b(?:only|just)\s+\$\d+\b',
            
            # Other patterns
            r'\bcasino\b',
            r'\b(?:buy|cheap|discount)\s+(?:now|viagra|pills)\b',
            r'\bwork\s+from\s+home\b'
        ]
        
        # Urgency words that increase spam score
        self.urgency_words = [
            'limited', 'special', 'urgent', 'hurry', 'quick', 'now', 'today',
            'act', 'click', 'call', 'expires', 'ending', 'last chance', 'final',
            'dont miss', 'dont wait', 'immediately', 'instant'
        ]
        
    def preprocess_text(self, text):
        return text.lower()

    def extract_phone_numbers(self, text):
        # Match various phone number formats
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',    # (123) 456-7890
            r'\+\d{1,2}\s*\d{3}[-.]?\d{3}[-.]?\d{4}',  # +1 123-456-7890
            r'\b\d{10}\b'  # 1234567890
        ]
        numbers = []
        for pattern in phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                numbers.append(match.group())
        return list(set(numbers))  # Remove duplicates

    def get_matched_patterns(self, text):
        matched = []
        text_lower = text.lower()
        
        # Check each pattern and add a user-friendly description if matched
        pattern_descriptions = {
            r'\b(?:free|win|won)\s+(?:money|prize|cash|gift)\b': 'Free money/prize claims',
            r'\b(?:urgent|emergency|immediate)\b': 'Urgency words',
            r'\b(?:limited|special)(?:\s+\w+){0,2}\s+(?:offer|time|deal)\b': 'Limited time offers',
            r'\b(?:act|click|call|buy|sign[- ]?up)\s+(?:now|today|immediately)\b': 'Pressure to act immediately',
            r'\b(?:credit|loan)\s+(?:card|approved|guaranteed|instant)\b': 'Credit/loan offers',
            r'\b\d+%\s+(?:off|discount|save)\b': 'Large discount offers',
            r'\b(?:only|just)\s+\$\d+\b': 'Price baiting',
            r'\b(?:password|account|security)\s+(?:expired|compromised|verify)\b': 'Account security threats'
        }
        
        for pattern, description in pattern_descriptions.items():
            if re.search(pattern, text_lower):
                matched.append(description)
        
        return matched

    def extract_features(self, text):
        features = {
            'has_url': bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)),
            'has_email': bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)),
            'has_phone': bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)),
            'caps_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            'exclamation_count': text.count('!'),
            'suspicious_patterns': sum(1 for pattern in self.spam_patterns if re.search(pattern, text.lower()))
        }
        return features

    def check_urls(self, text):
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        suspicious_urls = []
        
        for url in urls:
            try:
                parsed = urlparse(url)
                if any(keyword in parsed.netloc.lower() for keyword in ['free', 'win', 'prize', 'casino']):
                    suspicious_urls.append(url)
            except:
                continue
                
        return suspicious_urls

    def analyze_message(self, text):
        # Extract features
        features = self.extract_features(text)
        
        # Check for suspicious URLs
        suspicious_urls = self.check_urls(text)
        
        # Extract phone numbers
        extracted_numbers = self.extract_phone_numbers(text)
        
        # Get matched patterns
        suspicious_patterns = self.get_matched_patterns(text)
        
        # Calculate spam score based on features
        pattern_weight = 0.4
        url_weight = 0.2
        caps_weight = 0.1
        contact_weight = 0.15
        punctuation_weight = 0.15
        urgency_weight = 0.7
        
        # Calculate pattern score without division
        pattern_score = min(features['suspicious_patterns'], 1.0) * pattern_weight
        
        # Calculate urgency score based on urgency words
        text_lower = text.lower()
        urgency_count = sum(1 for word in self.urgency_words if word in text_lower)
        urgency_score = min(urgency_count / 2, 1.0) * urgency_weight
        
        # Other scores
        url_score = (len(suspicious_urls) > 0) * url_weight
        caps_score = (features['caps_ratio'] > 0.3) * caps_weight  # Lowered threshold
        contact_score = (features['has_email'] or features['has_phone']) * contact_weight  # Changed to OR
        punctuation_score = min(features['exclamation_count'] / 2, 1.0) * punctuation_weight  # Scale with count
        
        # Combine all scores
        spam_score = pattern_score + url_score + caps_score + contact_score + punctuation_score + urgency_score
        
        return {
            'is_spam': spam_score > 0.5,
            'spam_score': spam_score,
            'signals': {
                'pattern_matches': features['suspicious_patterns'],
                'suspicious_urls': suspicious_urls,
                'caps_ratio': features['caps_ratio'],
                'has_email': features['has_email'],
                'has_phone': features['has_phone'],
                'exclamation_count': features['exclamation_count'],
                'urgency_score': urgency_score
            },
            'extracted_numbers': extracted_numbers,
            'suspicious_patterns': suspicious_patterns
        }

    def update_model(self, text, is_spam):
        # This method is kept for compatibility but does nothing since we're using rule-based detection
        pass

