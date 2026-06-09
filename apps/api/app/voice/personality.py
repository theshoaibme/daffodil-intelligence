from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import time


class PersonalityTrait(Enum):
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    EMPATHETIC = "empathetic"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    ENCOURAGING = "encouraging"
    FORMAL = "formal"


class PersonalityMood(Enum):
    HAPPY = "happy"
    NEUTRAL = "neutral"
    SERIOUS = "serious"
    EXCITED = "excited"
    CARING = "caring"
    FOCUSED = "focused"
    RELAXED = "relaxed"
    MOTIVATIONAL = "motivational"


class SpeakingStyle(Enum):
    CONVERSATIONAL = "conversational"
    FORMAL = "formal"
    ACADEMIC = "academic"
    CASUAL = "casual"
    BRIEF = "brief"
    DETAILED = "detailed"


@dataclass
class PersonalityConfig:
    name: str = "Assistant"
    traits: List[PersonalityTrait] = field(default_factory=lambda: [PersonalityTrait.FRIENDLY])
    mood: PersonalityMood = PersonalityMood.NEUTRAL
    speaking_style: SpeakingStyle = SpeakingStyle.CONVERSATIONAL
    energy_level: float = 0.5
    empathy_level: float = 0.7
    humor_level: float = 0.3
    formality_level: float = 0.5
    creativity_level: float = 0.5
    enthusiasm_level: float = 0.7
    patience_level: float = 0.8
    confidence_level: float = 0.8


class PersonalityEngine:
    def __init__(self):
        self.current_personality = PersonalityConfig()
        self._mood_history: List[Dict] = []
        self._interaction_count = 0
        
        self.presets: Dict[str, PersonalityConfig] = {
            "friendly": PersonalityConfig(
                name="Friendly AI",
                traits=[PersonalityTrait.FRIENDLY, PersonalityTrait.EMPATHETIC],
                mood=PersonalityMood.HAPPY,
                speaking_style=SpeakingStyle.CONVERSATIONAL,
                energy_level=0.7,
                humor_level=0.4
            ),
            "professional": PersonalityConfig(
                name="Professional Assistant",
                traits=[PersonalityTrait.PROFESSIONAL, PersonalityTrait.ANALYTICAL],
                mood=PersonalityMood.SERIOUS,
                speaking_style=SpeakingStyle.FORMAL,
                energy_level=0.6,
                formality_level=0.8
            ),
            "humorous": PersonalityConfig(
                name="Fun Companion",
                traits=[PersonalityTrait.HUMOROUS, PersonalityTrait.FRIENDLY],
                mood=PersonalityMood.EXCITED,
                speaking_style=SpeakingStyle.CASUAL,
                energy_level=0.9,
                humor_level=0.8
            ),
            "empathetic": PersonalityConfig(
                name="Caring Listener",
                traits=[PersonalityTrait.EMPATHETIC, PersonalityTrait.ENCOURAGING],
                mood=PersonalityMood.CARING,
                speaking_style=SpeakingStyle.CONVERSATIONAL,
                empathy_level=0.9,
                patience_level=0.95
            ),
            "academic": PersonalityConfig(
                name="Scholar AI",
                traits=[PersonalityTrait.ANALYTICAL, PersonalityTrait.PROFESSIONAL],
                mood=PersonalityMood.FOCUSED,
                speaking_style=SpeakingStyle.ACADEMIC,
                formality_level=0.9,
                creativity_level=0.6
            ),
            "motivational": PersonalityConfig(
                name="Motivational Coach",
                traits=[PersonalityTrait.ENCOURAGING, PersonalityTrait.ENTHUSIASTIC],
                mood=PersonalityMood.MOTIVATIONAL,
                speaking_style=SpeakingStyle.CASUAL,
                energy_level=0.95,
                enthusiasm_level=0.95
            ),
            "calm": PersonalityConfig(
                name="Calm Advisor",
                traits=[PersonalityTrait.CALM, PersonalityTrait.EMPATHETIC],
                mood=PersonalityMood.RELAXED,
                speaking_style=SpeakingStyle.CONVERSATIONAL,
                energy_level=0.4,
                patience_level=0.95
            ),
            "creative": PersonalityConfig(
                name="Creative Partner",
                traits=[PersonalityTrait.CREATIVE, PersonalityTrait.HUMOROUS],
                mood=PersonalityMood.EXCITED,
                speaking_style=SpeakingStyle.CASUAL,
                creativity_level=0.95,
                humor_level=0.5
            ),
            "mentor": PersonalityConfig(
                name="Wise Mentor",
                traits=[PersonalityTrait.ANALYTICAL, PersonalityTrait.ENCOURAGING],
                mood=PersonalityMood.RELAXED,
                speaking_style=SpeakingStyle.DETAILED,
                formality_level=0.6,
                patience_level=0.95
            ),
            "companion": PersonalityConfig(
                name="Daily Companion",
                traits=[PersonalityTrait.FRIENDLY, PersonalityTrait.HUMOROUS, PersonalityTrait.EMPATHETIC],
                mood=PersonalityMood.HAPPY,
                speaking_style=SpeakingStyle.CONVERSATIONAL,
                energy_level=0.7,
                empathy_level=0.8,
                humor_level=0.5
            ),
        }
        
        self.greeting_templates = {
            PersonalityMood.HAPPY: [
                "Hello! Great to see you today! How can I help?",
                "Hey there! What can I do for you?",
                "Hi! I'm excited to help you out!",
                "Hello! Hope you're having an amazing day!"
            ],
            PersonalityMood.NEUTRAL: [
                "Hello. How can I assist you today?",
                "Hi there. What would you like help with?",
                "Hello. I'm here to help. What do you need?",
            ],
            PersonalityMood.SERIOUS: [
                "Good day. How may I help you?",
                "Hello. What do you need assistance with?",
                "Greetings. How can I be of service?",
            ],
            PersonalityMood.EXCITED: [
                "Wow, great to see you! What can I help you with today?!",
                "Hey! I'm so excited to help! What's up?",
                "Hello! This is going to be fun! What do you need?",
            ],
            PersonalityMood.CARING: [
                "Hello, friend. I'm here for you. What do you need?",
                "Hi there. Take your time, I'm here to help.",
                "Hello. I hope you're doing well. How can I assist?",
            ],
            PersonalityMood.MOTIVATIONAL: [
                "Let's do this! What are we working on today?",
                "Hey champion! Ready to make progress?",
                "Hi! I believe in you. Let's get started!",
            ],
            PersonalityMood.RELAXED: [
                "Hello there. Take your time, no rush.",
                "Hi. How can I help you relax today?",
                "Hello. Let's take it easy and figure this out.",
            ],
            PersonalityMood.FOCUSED: [
                "Hello. Ready to dive in and solve this.",
                "Hi. Let's focus and get this done efficiently.",
                "Greetings. What's the task at hand?",
            ],
        }
        
        self.encouragement_templates = {
            "good_progress": [
                "You're doing great! Keep going!",
                "Excellent work! Keep it up!",
                "You're making fantastic progress!",
            ],
            "keep_going": [
                "Don't give up! You're almost there!",
                "Keep pushing, you're doing well!",
                "Stay focused, you've got this!",
            ],
            "celebration": [
                "Fantastic! You did it!",
                "Amazing! Congratulations!",
                "Wonderful! Well done!",
            ],
            "understanding": [
                "I understand. Let me help you with that.",
                "I hear you. Here's what I suggest...",
                "I see. Let me clarify this for you.",
            ],
        }
        
        self.filler_words = {
            PersonalityTrait.FRIENDLY: ["great", "awesome", "sure thing", "absolutely"],
            PersonalityTrait.PROFESSIONAL: ["indeed", "certainly", "of course", "precisely"],
            PersonalityTrait.HUMOROUS: ["oh boy", "here we go", "fun fact", "guess what"],
            PersonalityTrait.EMPATHETIC: ["I understand", "I hear you", "that's completely normal"],
            PersonalityTrait.ANALYTICAL: ["logically", "essentially", "fundamentally", "technically"],
            PersonalityTrait.CREATIVE: ["imagine", "what if", "here's a thought", "fun idea"],
        }
        
        self.bengali_greetings = {
            PersonalityMood.HAPPY: ["হ্যালো! আজ কেমন আছো?", "ওহে! তোমার জন্য কি করতে পারি?"],
            PersonalityMood.NEUTRAL: ["হ্যালো। আমি কিভাবে সাহায্য করতে পারি?", "হ্যালো। কি প্রয়োজন?"],
            PersonalityMood.EXCITED: ["ওয়াও! তুমি এসেছ! চলো শুরু করি!", "হাই! আমি খুবই উত্তেজিত!"],
        }
    
    def set_preset(self, preset_name: str) -> bool:
        if preset_name in self.presets:
            self.current_personality = self.presets[preset_name]
            return True
        return False
    
    def get_presets(self) -> List[str]:
        return list(self.presets.keys())
    
    def set_mood(self, mood: PersonalityMood):
        self.current_personality.mood = mood
        self._mood_history.append({
            "mood": mood.value,
            "timestamp": time.time(),
            "interaction": self._interaction_count
        })
    
    def add_trait(self, trait: PersonalityTrait):
        if trait not in self.current_personality.traits:
            self.current_personality.traits.append(trait)
    
    def remove_trait(self, trait: PersonalityTrait):
        if trait in self.current_personality.traits:
            self.current_personality.traits.remove(trait)
    
    def set_energy_level(self, level: float):
        self.current_personality.energy_level = max(0, min(1, level))
    
    def generate_greeting(self, language: str = "en") -> str:
        if language.startswith("bn"):
            templates = self.bengali_greetings.get(
                self.current_personality.mood,
                self.bengali_greetings[PersonalityMood.NEUTRAL]
            )
            return random.choice(templates)
        
        templates = self.greeting_templates.get(
            self.current_personality.mood,
            self.greeting_templates[PersonalityMood.NEUTRAL]
        )
        return random.choice(templates)
    
    def get_filler_word(self) -> str:
        fillers = []
        for trait in self.current_personality.traits:
            if trait in self.filler_words:
                fillers.extend(self.filler_words[trait])
        
        if fillers:
            return random.choice(fillers)
        return ""
    
    def modify_response(self, response: str) -> str:
        personality = self.current_personality
        
        if PersonalityTrait.HUMOROUS in personality.traits and personality.humor_level > 0.5:
            response = self._add_humor(response)
        
        if PersonalityTrait.FRIENDLY in personality.traits:
            response = self._add_friendliness(response)
        
        if PersonalityTrait.EMPATHETIC in personality.traits:
            response = self._add_empathy(response)
        
        if personality.formality_level > 0.7:
            response = self._make_formal(response)
        elif personality.formality_level < 0.3:
            response = self._make_casual(response)
        
        if personality.enthusiasm_level > 0.7:
            response = self._add_enthusiasm(response)
        
        return response
    
    def _add_humor(self, text: str) -> str:
        humor_gags = [
            " (Kidding! Or am I?)",
            " - just like my creator says!",
            " Pretty cool, right?",
            " Don't tell anyone I said that!",
            " That escalated quickly!",
        ]
        
        if len(text) > 20 and random.random() < 0.3:
            gag = random.choice(humor_gags)
            sentences = text.split('.')
            if len(sentences) > 0:
                sentences[-1] = sentences[-1] + gag
                text = '.'.join(sentences)
        
        return text
    
    def _add_friendliness(self, text: str) -> str:
        fillers = ["Sure thing!", "Great question!", "Absolutely!", "Of course!"]
        
        if text and not any(f in text.lower() for f in fillers):
            prefix = random.choice(fillers) + " "
            if text[0].isupper():
                return prefix + text
        return text
    
    def _add_empathy(self, text: str) -> str:
        empathy_phrases = [
            "I understand this might be challenging.",
            "I know this can be overwhelming.",
            "You're doing great by asking about this.",
            "It's completely normal to have these questions.",
        ]
        
        if random.random() < 0.2:
            prefix = random.choice(empathy_phrases) + " "
            return prefix + text
        return text
    
    def _make_formal(self, text: str) -> str:
        replacements = {
            "yeah": "yes",
            "okay": "certainly",
            "hi": "good day",
            "hey": "hello",
            "cool": "excellent",
            "awesome": "wonderful",
            "gonna": "going to",
            "wanna": "want to",
            "gotta": "have to",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _make_casual(self, text: str) -> str:
        replacements = {
            "certainly": "sure",
            "therefore": "so",
            "however": "but",
            "additionally": "also",
            "consequently": "so",
            "nevertheless": "still",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _add_enthusiasm(self, text: str) -> str:
        if self.current_personality.mood == PersonalityMood.EXCITED:
            exclamations = ["That's amazing!", "Fantastic!", "Wonderful!"]
            if not any(e in text for e in exclamations):
                text += " " + random.choice(exclamations)
        
        return text
    
    def get_encouragement(self, context: str = "good_progress") -> str:
        templates = self.encouragement_templates.get(context, self.encouragement_templates["keep_going"])
        return random.choice(templates)
    
    def respond_to_emotion(self, detected_emotion: str) -> str:
        responses = {
            "frustrated": "I understand this might be frustrating. Let's work through this together. Take a deep breath, and we'll figure it out.",
            "confused": "No worries! Let me clarify this for you. Sometimes things can be a bit tricky to understand.",
            "excited": "I love your enthusiasm! Let me help you make the most of this excitement!",
            "happy": "It's wonderful to see you happy! How can I help make your day even better?",
            "sad": "I'm here for you. Sometimes talking through things can help. What would you like to discuss?",
            "curious": "What a great question! I love curious minds! Let me explain this in detail.",
        }
        
        return responses.get(detected_emotion, "I'm here to help! What would you like to know?")
    
    def adjust_based_on_feedback(self, positive: bool):
        self._interaction_count += 1
        
        if positive:
            if self.current_personality.energy_level < 1.0:
                self.current_personality.energy_level += 0.05
            if self.current_personality.humor_level < 1.0:
                self.current_personality.humor_level += 0.02
        else:
            if self.current_personality.energy_level > 0.3:
                self.current_personality.energy_level -= 0.03
            if self.current_personality.empathy_level < 1.0:
                self.current_personality.empathy_level += 0.02
    
    def get_mood_history(self) -> List[Dict]:
        return self._mood_history[-20:]
    
    def get_current_config(self) -> Dict[str, Any]:
        return {
            "name": self.current_personality.name,
            "traits": [t.value for t in self.current_personality.traits],
            "mood": self.current_personality.mood.value,
            "speaking_style": self.current_personality.speaking_style.value,
            "energy_level": self.current_personality.energy_level,
            "humor_level": self.current_personality.humor_level,
            "formality_level": self.current_personality.formality_level,
            "empathy_level": self.current_personality.empathy_level,
            "creativity_level": self.current_personality.creativity_level,
            "enthusiasm_level": self.current_personality.enthusiasm_level,
        }
    
    def set_custom_config(self, **kwargs):
        if "name" in kwargs:
            self.current_personality.name = kwargs["name"]
        if "energy_level" in kwargs:
            self.current_personality.energy_level = max(0, min(1, float(kwargs["energy_level"])))
        if "humor_level" in kwargs:
            self.current_personality.humor_level = max(0, min(1, float(kwargs["humor_level"])))
        if "formality_level" in kwargs:
            self.current_personality.formality_level = max(0, min(1, float(kwargs["formality_level"])))
        if "empathy_level" in kwargs:
            self.current_personality.empathy_level = max(0, min(1, float(kwargs["empathy_level"])))
        if "creativity_level" in kwargs:
            self.current_personality.creativity_level = max(0, min(1, float(kwargs["creativity_level"])))
        if "enthusiasm_level" in kwargs:
            self.current_personality.enthusiasm_level = max(0, min(1, float(kwargs["enthusiasm_level"])))


personality_engine = PersonalityEngine()