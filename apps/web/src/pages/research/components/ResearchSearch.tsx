import { useState, useEffect, useRef } from "react";
import { Search, FileText, Plus } from "lucide-react";
import { ResearchPaper } from "./types";
import { ResearchPaperCard } from "./ResearchPaperCard";
import { AddPaperModal } from "./AddPaperModal";
import { ResearchDropdown } from "./ResearchDropdown";
import { ResearchPagination } from "./ResearchPagination";

export function ResearchSearch() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const categories = ["All", "Computer Science", "AI & Education", "Smart Grids"];

  const [papers, setPapers] = useState<ResearchPaper[]>([
    {
      title: "Attention Is All You Need",
      authors: "Vaswani et al.",
      year: "2017",
      citations: 124500,
      source: "NeurIPS",
      category: "Computer Science",
      abstract: "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
      url: "https://arxiv.org/abs/1706.03762"
    },
    {
      title: "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
      authors: "Devlin et al.",
      year: "2018",
      citations: 98300,
      source: "NAACL",
      category: "Computer Science",
      abstract: "We introduce a new language representation model called BERT. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations.",
      url: "https://arxiv.org/abs/1810.04805"
    },
    {
      title: "Language Models are Few-Shot Learners",
      authors: "Brown et al. (OpenAI)",
      year: "2020",
      citations: 28400,
      source: "NeurIPS",
      category: "AI & Education",
      abstract: "We show that scaling language models greatly improves task-agnostic, few-shot performance, sometimes even competitive with prior state-of-the-art fine-tuning approaches.",
      url: "https://arxiv.org/abs/2005.14165"
    },
    {
      title: "Deep Residual Learning for Image Recognition",
      authors: "He et al. (Microsoft)",
      year: "2015",
      citations: 186400,
      source: "CVPR",
      category: "Computer Science",
      abstract: "We present a residual learning framework to ease the training of networks that are substantially deeper than those previously used. We evaluate it on ImageNet.",
      url: "https://arxiv.org/abs/1512.03385"
    },
    {
      title: "Generative Adversarial Nets",
      authors: "Goodfellow et al.",
      year: "2014",
      citations: 74200,
      source: "NeurIPS",
      category: "Computer Science",
      abstract: "We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model and a discriminative model.",
      url: "https://arxiv.org/abs/1406.2661"
    },
    {
      title: "Instruction Tuning for Large Language Models: A Survey",
      authors: "Zhang et al.",
      year: "2023",
      citations: 820,
      source: "arXiv",
      category: "AI & Education",
      abstract: "This paper provides a systematic review of instruction tuning in large language models, discussing datasets, methodologies, and benchmarks for human alignment.",
      url: "https://arxiv.org/abs/2308.10792"
    },
    {
      title: "Comparison of Quantum Cryptography Protocols in Smart Grids",
      authors: "Siddique et al.",
      year: "2024",
      citations: 45,
      source: "IEEE Trans",
      category: "Smart Grids",
      abstract: "We evaluate BB84, E91, and B92 protocols in power transmission grids under noise constraints, providing real-world key generation rate comparisons.",
      url: "https://ieeexplore.ieee.org/document/10423"
    },
    {
      title: "Deep Reinforcement Learning for Smart Grid Load Balancing",
      authors: "Wang et al.",
      year: "2022",
      citations: 310,
      source: "IEEE SmartGrid",
      category: "Smart Grids",
      abstract: "A deep Q-learning approach to dynamic load dispatching in microgrids to minimize peaks, showing an 18% cost reduction compared to legacy heuristic methods.",
      url: "https://ieeexplore.ieee.org/document/9082"
    },
    {
      title: "AI-Augmented Syllabus Design in Higher Education",
      authors: "Miller et al.",
      year: "2025",
      citations: 12,
      source: "J. Ed. Tech",
      category: "AI & Education",
      abstract: "Evaluating standard and agent-synthesized curricula in undergraduate computer science programs. Results show improved engagement rates with personalized pathways.",
      url: "https://doi.org/10.1016/j.edurev"
    }
  ]);

  const topSearches = [
    "Deep Learning in CS",
    "Smart Grids Optimization",
    "Academic Writing Formats",
  ];

  const recentResearchSearches = [
    "Attention Is All You Need",
    "BERT: Pre-training of Deep Bidirectional Transformers",
    "Comparison of Quantum Cryptography Protocols in Smart Grids",
  ];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredPapers = papers.filter((item) => {
    const matchesSearch = 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.authors.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.abstract.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Reset page to 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCategory]);

  // Pagination Settings
  const itemsPerPage = 6;
  const totalPages = Math.ceil(filteredPapers.length / itemsPerPage);
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredPapers.slice(indexOfFirstItem, indexOfLastItem);

  const handleAddPaper = (newPaperData: Omit<ResearchPaper, "citations">) => {
    const newPaperItem: ResearchPaper = {
      ...newPaperData,
      citations: 0,
    };
    setPapers([newPaperItem, ...papers]);
  };

  const handleSelectSearch = (term: string) => {
    setSearchQuery(term);
    setIsDropdownOpen(false);
  };

  return (
    <div className="space-y-6 sm:space-y-8 relative">
      {/* Centered Search & Category Filter Section */}
      <div className="flex flex-col items-center gap-4 text-center relative z-20 max-w-2xl mx-auto">
        <div ref={searchRef} className="relative w-full">
          <div className="relative w-full">
            <Search
              size={20}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant/60 pointer-events-none"
            />
            <input
              type="text"
              value={searchQuery}
              onFocus={() => setIsDropdownOpen(true)}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search papers by title, author, abstract..."
              className="w-full bg-surface-container-lowest rounded-full pl-12 pr-6 py-3.5 text-base text-on-surface placeholder:text-on-surface-variant/75 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent outline-none border border-outline-variant/10 shadow-sm transition-all"
            />
          </div>

          {isDropdownOpen && (
            <ResearchDropdown
              topSearches={topSearches}
              recentResearchSearches={recentResearchSearches}
              onSelectSearch={handleSelectSearch}
            />
          )}
        </div>
        
        <div className="flex flex-wrap justify-center gap-2 mt-1">
          {categories.map((cat) => {
            const isActive = selectedCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-5 py-2 rounded-full text-xs sm:text-sm font-semibold tracking-wide transition-all duration-200 cursor-pointer ${
                  isActive 
                    ? "bg-primary text-on-primary shadow-sm scale-105" 
                    : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high"
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Grid View of Research Paper Cards */}
      <div className="space-y-6 relative z-10 text-left">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-lg sm:text-xl font-semibold text-on-surface flex items-center gap-2">
            <FileText className="text-primary" size={20} />
            Research Library ({filteredPapers.length})
          </h3>
        </div>
        
        {currentItems.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {currentItems.map((paper, idx) => (
              <ResearchPaperCard key={idx} paper={paper} />
            ))}
          </div>
        ) : (
          <div className="p-12 text-center bg-surface-container-low/30 rounded-3xl border border-dashed border-outline-variant/20 text-on-surface-variant">
            No papers match your search queries.
          </div>
        )}
      </div>

      {/* Pagination & Add Paper Action bar */}
      {filteredPapers.length > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-8 pt-4 border-t border-outline-variant/10 relative z-10">
          
          <ResearchPagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />

          {/* Add Paper Control */}
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary text-on-primary font-semibold text-xs sm:text-sm hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
          >
            <Plus size={16} />
            Add Research Paper
          </button>
        </div>
      )}

      {/* Add Research Paper Modal */}
      <AddPaperModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={handleAddPaper}
      />

    </div>
  );
}

