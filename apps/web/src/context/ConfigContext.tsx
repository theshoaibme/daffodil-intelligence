import React, { createContext, useContext, useState } from 'react';

export type Language = 'bn' | 'en' | 'auto';

interface ConfigContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  effectiveLanguage: 'bn' | 'en';
  detectedLanguage: 'bn' | 'en';
  voiceModel: string;
  setVoiceModel: (model: string) => void;
  voiceMode: 'streaming' | 'standard';
  setVoiceMode: (mode: 'streaming' | 'standard') => void;
  agentMemory: Record<string, any>;
  updateAgentMemory: (key: string, value: any) => void;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (!context) throw new Error('useConfig must be used within ConfigProvider');
  return context;
};

const LANGUAGES: Record<string, string> = {
  bn: 'বাংলা',
  en: 'English',
  auto: 'Auto Detect',
};

export const detectLanguage = (text: string): 'bn' | 'en' => {
  const bengaliRegex = /[\u0980-\u09FF]/;
  if (bengaliRegex.test(text)) return 'bn';
  return 'en';
};

export const getLanguageLabel = (lang: Language): string => LANGUAGES[lang] || lang;

export const ConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('di_language');
    if (saved === 'bn' || saved === 'en' || saved === 'auto') return saved;
    return 'auto';
  });

  const [detectedLanguage] = useState<'bn' | 'en'>(() => {
    const saved = localStorage.getItem('di_detected_lang');
    if (saved === 'bn' || saved === 'en') return saved;
    return 'bn';
  });

  const [voiceModel, setVoiceModel] = useState(() => {
    return localStorage.getItem('di_voice_model') || 'Aoede';
  });

  const [voiceMode, setVoiceMode] = useState<'streaming' | 'standard'>(() => {
    return (localStorage.getItem('di_voice_mode') as 'streaming' | 'standard') || 'streaming';
  });

  const [agentMemory, setAgentMemory] = useState<Record<string, any>>(() => {
    try {
      const saved = localStorage.getItem('di_agent_memory');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  const effectiveLanguage = language === 'auto' ? detectedLanguage : language;

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('di_language', lang);
  };

  const updateAgentMemory = (key: string, value: any) => {
    setAgentMemory(prev => {
      const updated = { ...prev, [key]: value };
      localStorage.setItem('di_agent_memory', JSON.stringify(updated));
      return updated;
    });
  };

  return (
    <ConfigContext.Provider value={{
      language,
      setLanguage,
      effectiveLanguage,
      detectedLanguage,
      voiceModel,
      setVoiceModel,
      voiceMode,
      setVoiceMode,
      agentMemory,
      updateAgentMemory,
    }}>
      {children}
    </ConfigContext.Provider>
  );
};