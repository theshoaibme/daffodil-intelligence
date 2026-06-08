import React, { useState, useEffect } from "react";
import { ArrowLeft, Plus, Trash2, Key, Database, Cpu, CheckCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ModelInfo, DEFAULT_MODELS, getModels } from "./PromptBar/ModelSelector";

export function ModelManagementPage() {
  const navigate = useNavigate();
  const [models, setModels] = useState<ModelInfo[]>([]);
  
  // Custom Model Form state
  const [name, setName] = useState("");
  const [provider, setProvider] = useState("OpenAI");
  const [customProvider, setCustomProvider] = useState("");
  const [apiUrl, setApiUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  
  const [geminiKey, setGeminiKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [claudeKey, setClaudeKey] = useState("");
  
  // Alert/Status state
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load models and credentials on mount
  useEffect(() => {
    setModels(getModels());
    
    // Load API keys
    setGeminiKey(localStorage.getItem("daffodil_api_key_gemini") || "");
    setOpenaiKey(localStorage.getItem("daffodil_api_key_openai") || "");
    setClaudeKey(localStorage.getItem("daffodil_api_key_claude") || "");
  }, []);

  const triggerNotification = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => {
      setSuccessMessage(null);
    }, 3000);
  };

  const handleSaveApiKeys = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem("daffodil_api_key_gemini", geminiKey);
    localStorage.setItem("daffodil_api_key_openai", openaiKey);
    localStorage.setItem("daffodil_api_key_claude", claudeKey);
    triggerNotification("Provider API keys saved successfully!");
  };

  const handleAddCustomModel = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const finalProvider = provider === "Custom" ? customProvider.trim() || "Custom" : provider;
    const newModelId = `custom-${finalProvider.toLowerCase()}-${name.toLowerCase().replace(/\s+/g, "-")}-${Date.now()}`;
    
    const newModel: ModelInfo = {
      id: newModelId,
      name: name.trim(),
      provider: finalProvider,
      isCustom: true,
      apiUrl: apiUrl.trim() || undefined,
      apiKey: apiKey.trim() || undefined
    };

    try {
      const existingCustom = localStorage.getItem("daffodil_custom_models");
      const customList = existingCustom ? JSON.parse(existingCustom) : [];
      const updatedList = [...customList, newModel];
      localStorage.setItem("daffodil_custom_models", JSON.stringify(updatedList));
      
      // Update local state
      setModels([...DEFAULT_MODELS, ...updatedList]);
      
      // Clear form
      setName("");
      setApiUrl("");
      setApiKey("");
      if (provider === "Custom") {
        setCustomProvider("");
      }
      
      triggerNotification(`Custom model "${newModel.name}" added successfully!`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteModel = (id: string) => {
    try {
      const existingCustom = localStorage.getItem("daffodil_custom_models");
      if (existingCustom) {
        const customList = JSON.parse(existingCustom) as ModelInfo[];
        const updatedList = customList.filter(m => m.id !== id);
        localStorage.setItem("daffodil_custom_models", JSON.stringify(updatedList));
        setModels([...DEFAULT_MODELS, ...updatedList]);
        triggerNotification("Custom model deleted.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-background dot-pattern text-on-surface flex flex-col font-sans">
      {/* Success Notification Alert */}
      <AnimatePresence>
        {successMessage && (
          <motion.div
            initial={{ opacity: 0, y: -50, scale: 0.9 }}
            animate={{ opacity: 1, y: 20, scale: 1 }}
            exit={{ opacity: 0, y: -50, scale: 0.9 }}
            className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 bg-surface-container border border-primary/20 shadow-xl rounded-full px-6 py-3 flex items-center gap-3"
          >
            <CheckCircle className="text-primary" size={20} />
            <span className="text-sm font-medium">{successMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Top Header */}
      <header className="px-6 py-4 flex items-center justify-between border-b border-outline-variant/20 bg-surface-container-lowest/80 backdrop-blur-md sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate("/intelligence")}
            className="p-2 rounded-full hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all cursor-pointer border-0 outline-none"
          >
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-xl font-semibold tracking-tight">Model Management</h1>
        </div>
      </header>

      {/* Main Grid Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Forms Column */}
        <div className="lg:col-span-7 space-y-8">
          
          {/* Card 1: Add Custom Model */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-surface-container-low border border-outline-variant/30 rounded-3xl p-6 shadow-sm"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 rounded-2xl bg-primary/10 text-primary">
                <Cpu size={22} />
              </div>
              <div>
                <h2 className="text-lg font-medium">Add Custom Model</h2>
                <p className="text-xs text-on-surface-variant">Connect your custom API or deployment</p>
              </div>
            </div>

            <form onSubmit={handleAddCustomModel} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-on-surface-variant/80">Model Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Llama 3 70B"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="bg-surface-container-high/60 border border-outline-variant/30 rounded px-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-on-surface-variant/80">Provider / Host</label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="bg-surface-container-high/60 border border-outline-variant/30 rounded px-4 py-2.5 text-sm text-on-surface focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all cursor-pointer"
                  >
                    <option value="OpenAI">OpenAI</option>
                    <option value="Gemini">Gemini</option>
                    <option value="Claude">Claude</option>
                    <option value="Ollama">Ollama</option>
                    <option value="OpenRouter">OpenRouter</option>
                    <option value="Custom">Custom Provider</option>
                  </select>
                </div>
              </div>

              {provider === "Custom" && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="flex flex-col gap-1.5"
                >
                  <label className="text-xs font-semibold text-on-surface-variant/80">Custom Provider Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. LocalLLM"
                    value={customProvider}
                    onChange={(e) => setCustomProvider(e.target.value)}
                    className="bg-surface-container-high/60 border border-outline-variant/30 rounded px-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                  />
                </motion.div>
              )}

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-on-surface-variant/80">API Endpoint URL (Optional)</label>
                <input
                  type="url"
                  placeholder="e.g. http://localhost:11434/v1"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  className="bg-surface-container-high/60 border border-outline-variant/30 rounded px-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-on-surface-variant/80">API Key / Token (Optional)</label>
                <input
                  type="password"
                  placeholder="Leave blank to use provider key settings"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="bg-surface-container-high/60 border border-outline-variant/30 rounded px-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
              </div>

              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 bg-primary text-on-primary rounded-xl py-3 text-sm font-semibold hover:bg-primary-container hover:shadow-md cursor-pointer border-0 outline-none transition-all mt-2"
              >
                <Plus size={18} />
                Add Custom Model
              </button>
            </form>
          </motion.div>

          {/* Card 2: Configure Provider Keys */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="bg-surface-container-low border border-outline-variant/30 rounded-3xl p-6 shadow-sm"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 rounded-2xl bg-primary/10 text-primary">
                <Key size={22} />
              </div>
              <div>
                <h2 className="text-lg font-medium">Provider API Credentials</h2>
                <p className="text-xs text-on-surface-variant">Manage global keys for standard models</p>
              </div>
            </div>

            <form onSubmit={handleSaveApiKeys} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-on-surface-variant/80">Gemini API Key</label>
                <input
                  type="password"
                  placeholder="Enter Gemini API key"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="bg-surface-container-high/60 border border-outline-variant/30 rounded px-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-on-surface-variant/80">OpenAI API Key</label>
                <input
                  type="password"
                  placeholder="Enter OpenAI API key"
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="bg-surface-container-high/60 border border-outline-variant/30 rounded px-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-on-surface-variant/80">Claude API Key</label>
                <input
                  type="password"
                  placeholder="Enter Anthropic Claude API key"
                  value={claudeKey}
                  onChange={(e) => setClaudeKey(e.target.value)}
                  className="bg-surface-container-high/60 border border-outline-variant/30 rounded px-4 py-2.5 text-sm text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-primary text-on-primary rounded-xl py-3 text-sm font-semibold hover:bg-primary-container hover:shadow-md cursor-pointer border-0 outline-none transition-all mt-2"
              >
                Save Credentials
              </button>
            </form>
          </motion.div>
        </div>

        {/* Right Side: Active Models List Column */}
        <div className="lg:col-span-5 space-y-8">
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-surface-container-low border border-outline-variant/30 rounded-3xl p-6 shadow-sm flex flex-col h-[670px]"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 rounded-2xl bg-primary/10 text-primary">
                <Database size={22} />
              </div>
              <div>
                <h2 className="text-lg font-medium">Available Models</h2>
                <p className="text-xs text-on-surface-variant">Default and custom configured models</p>
              </div>
            </div>

            {/* Model List Viewport */}
            <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2 pr-1">
              {models.map((model) => (
                <div 
                  key={model.id}
                  className="flex items-center justify-between p-3.5 bg-surface-container-high/40 border border-outline-variant/20 hover:border-outline-variant/50 rounded-2xl transition-all"
                >
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm font-medium">{model.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-on-surface-variant">{model.provider}</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold ${
                        model.isCustom 
                          ? "bg-tertiary/10 text-tertiary" 
                          : "bg-primary/10 text-primary"
                      }`}>
                        {model.isCustom ? "Custom" : "System"}
                      </span>
                    </div>
                  </div>

                  {model.isCustom && (
                    <button
                      onClick={() => handleDeleteModel(model.id)}
                      className="p-2 text-on-surface-variant hover:text-error hover:bg-error/10 rounded-xl transition-all cursor-pointer border-0 outline-none"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
