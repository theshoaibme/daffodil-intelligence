import { ResearchPaper } from "./types";

export const CATEGORIES = [
  "All",
  "Computer Science",
  "AI & Education",
  "Machine Learning",
  "Natural Language Processing",
  "Computer Vision",
  "Smart Grids",
  "Cybersecurity",
  "Bioinformatics",
  "Quantum Computing",
  "Robotics",
  "Data Science",
];

export const PAPER_CATEGORIES = CATEGORIES.filter((c) => c !== "All");

let _papers: ResearchPaper[] = [
  {
    id: "attention-2017",
    title: "Attention Is All You Need",
    authors: "Vaswani, A., Shazeer, N., Parmar, N., et al.",
    year: "2017",
    citations: 124500,
    source: "NeurIPS",
    category: "Natural Language Processing",
    abstract:
      "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
    url: "https://arxiv.org/abs/1706.03762",
    tags: ["transformer", "attention", "NLP", "sequence modeling"],
  },
  {
    id: "bert-2018",
    title: "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
    authors: "Devlin, J., Chang, M. W., Lee, K., & Toutanova, K.",
    year: "2018",
    citations: 98300,
    source: "NAACL",
    category: "Natural Language Processing",
    abstract:
      "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
    url: "https://arxiv.org/abs/1810.04805",
    tags: ["BERT", "pre-training", "bidirectional", "language model"],
  },
  {
    id: "gpt3-2020",
    title: "Language Models are Few-Shot Learners",
    authors: "Brown, T., Mann, B., Ryder, N., et al. (OpenAI)",
    year: "2020",
    citations: 28400,
    source: "NeurIPS",
    category: "AI & Education",
    abstract:
      "We show that scaling language models greatly improves task-agnostic, few-shot performance, sometimes even competitive with prior state-of-the-art fine-tuning approaches. GPT-3, with 175 billion parameters, achieves strong performance on NLP datasets including translation, question answering, and cloze tasks.",
    url: "https://arxiv.org/abs/2005.14165",
    tags: ["GPT-3", "few-shot", "large language model", "scaling"],
  },
  {
    id: "resnet-2015",
    title: "Deep Residual Learning for Image Recognition",
    authors: "He, K., Zhang, X., Ren, S., & Sun, J. (Microsoft)",
    year: "2015",
    citations: 186400,
    source: "CVPR",
    category: "Computer Vision",
    abstract:
      "We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions. We provide comprehensive empirical evidence showing that these residual networks are easier to optimize and can gain accuracy from considerably increased depth.",
    url: "https://arxiv.org/abs/1512.03385",
    tags: ["ResNet", "residual learning", "image recognition", "deep learning"],
  },
  {
    id: "gan-2014",
    title: "Generative Adversarial Nets",
    authors: "Goodfellow, I., Pouget-Abadie, J., Mirza, M., et al.",
    year: "2014",
    citations: 74200,
    source: "NeurIPS",
    category: "Machine Learning",
    abstract:
      "We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G that captures the data distribution, and a discriminative model D that estimates the probability that a sample came from the training data rather than G.",
    url: "https://arxiv.org/abs/1406.2661",
    tags: ["GAN", "generative model", "adversarial training"],
  },
  {
    id: "instruct-tuning-2023",
    title: "Instruction Tuning for Large Language Models: A Survey",
    authors: "Zhang, S., Dong, L., Li, X., et al.",
    year: "2023",
    citations: 820,
    source: "arXiv",
    category: "AI & Education",
    abstract:
      "This paper provides a systematic review of instruction tuning in large language models, discussing datasets, methodologies, and benchmarks for human alignment. We cover approaches from FLAN to InstructGPT, with a comprehensive taxonomy of instruction datasets.",
    url: "https://arxiv.org/abs/2308.10792",
    tags: ["instruction tuning", "RLHF", "alignment", "survey"],
  },
  {
    id: "quantum-grids-2024",
    title: "Comparison of Quantum Cryptography Protocols in Smart Grids",
    authors: "Siddique, U., Rahman, M., & Islam, R.",
    year: "2024",
    citations: 45,
    source: "IEEE Trans",
    category: "Smart Grids",
    abstract:
      "We evaluate BB84, E91, and B92 protocols in power transmission grids under noise constraints, providing real-world key generation rate comparisons and security assessments for critical infrastructure protection.",
    url: "https://ieeexplore.ieee.org/document/10423",
    tags: ["quantum cryptography", "smart grid", "BB84", "security"],
  },
  {
    id: "rl-grid-2022",
    title: "Deep Reinforcement Learning for Smart Grid Load Balancing",
    authors: "Wang, X., Li, Y., & Chen, Z.",
    year: "2022",
    citations: 310,
    source: "IEEE SmartGrid",
    category: "Smart Grids",
    abstract:
      "A deep Q-learning approach to dynamic load dispatching in microgrids to minimize peaks, showing an 18% cost reduction compared to legacy heuristic methods. Our approach adapts to real-time demand fluctuations using a continuous action space.",
    url: "https://ieeexplore.ieee.org/document/9082",
    tags: ["reinforcement learning", "smart grid", "load balancing", "deep Q-learning"],
  },
  {
    id: "ai-syllabus-2025",
    title: "AI-Augmented Syllabus Design in Higher Education",
    authors: "Miller, A., Thompson, R., & Garcia, L.",
    year: "2025",
    citations: 12,
    source: "J. Ed. Tech",
    category: "AI & Education",
    abstract:
      "Evaluating standard and agent-synthesized curricula in undergraduate computer science programs. Results show improved engagement rates with personalized pathways and a 22% improvement in learning outcome assessments.",
    url: "https://doi.org/10.1016/j.edurev",
    tags: ["AI in education", "curriculum design", "personalized learning"],
  },
  {
    id: "diffusion-2020",
    title: "Denoising Diffusion Probabilistic Models",
    authors: "Ho, J., Jain, A., & Abbeel, P.",
    year: "2020",
    citations: 18900,
    source: "NeurIPS",
    category: "Machine Learning",
    abstract:
      "We present high quality image synthesis results using diffusion probabilistic models, a class of latent variable models inspired by considerations from nonequilibrium thermodynamics. Our best results are obtained by training on a weighted variational bound designed according to a novel connection between diffusion probabilistic models and denoising score matching with Langevin dynamics.",
    url: "https://arxiv.org/abs/2006.11239",
    tags: ["diffusion model", "image generation", "DDPM", "score matching"],
  },
  {
    id: "vit-2020",
    title: "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
    authors: "Dosovitskiy, A., Beyer, L., Kolesnikov, A., et al. (Google Brain)",
    year: "2020",
    citations: 34200,
    source: "ICLR",
    category: "Computer Vision",
    abstract:
      "While the Transformer architecture has become the de-facto standard for NLP tasks, its applications to computer vision remain limited. In vision, attention is either applied in conjunction with convolutional networks, or used to replace certain components of convolutional networks while keeping their overall structure in place.",
    url: "https://arxiv.org/abs/2010.11929",
    tags: ["Vision Transformer", "ViT", "image classification", "attention"],
  },
  {
    id: "alphafold-2021",
    title: "Highly Accurate Protein Structure Prediction with AlphaFold",
    authors: "Jumper, J., Evans, R., Pritzel, A., et al. (DeepMind)",
    year: "2021",
    citations: 22400,
    source: "Nature",
    category: "Bioinformatics",
    abstract:
      "We developed AlphaFold, an AI system that predicts a protein's 3D structure from its amino acid sequence with atomic-level accuracy. This is a major scientific challenge that has resisted progress for 50 years. AlphaFold's prediction results are competitive with results from experimental techniques in many cases.",
    url: "https://www.nature.com/articles/s41586-021-03819-2",
    tags: ["protein structure", "AlphaFold", "bioinformatics", "deep learning"],
  },
  {
    id: "llama-2023",
    title: "LLaMA: Open and Efficient Foundation Language Models",
    authors: "Touvron, H., Lavril, T., Izacard, G., et al. (Meta AI)",
    year: "2023",
    citations: 6100,
    source: "arXiv",
    category: "Natural Language Processing",
    abstract:
      "We introduce LLaMA, a collection of foundation language models ranging from 7B to 65B parameters. We train our models on trillions of tokens, and show that it is possible to train state-of-the-art models using publicly available datasets exclusively.",
    url: "https://arxiv.org/abs/2302.13971",
    tags: ["LLaMA", "open source", "language model", "foundation model"],
  },
  {
    id: "ransomware-detect-2023",
    title: "Ransomware Detection Using Deep Neural Networks: A Behavioral Analysis",
    authors: "Kara, I., & Aydos, M.",
    year: "2023",
    citations: 178,
    source: "IEEE Access",
    category: "Cybersecurity",
    abstract:
      "This study proposes a deep learning-based ransomware detection framework that analyzes API call sequences and file system behaviors. Our model achieves 98.4% accuracy on a balanced dataset of 18,000 malware samples across 22 ransomware families.",
    url: "https://ieeexplore.ieee.org/document/10212",
    tags: ["ransomware", "malware detection", "deep learning", "cybersecurity"],
  },
  {
    id: "quantum-ml-2022",
    title: "Quantum Machine Learning: A Classical Perspective",
    authors: "Ciliberto, C., Herbster, M., Ialongo, A. D., et al.",
    year: "2022",
    citations: 1540,
    source: "Proc. Royal Soc.",
    category: "Quantum Computing",
    abstract:
      "We critically analyze the potential for quantum speedup in machine learning tasks. We discuss the opportunities and limitations of quantum computing for kernel methods, optimization, and sampling-based algorithms, providing a balanced assessment of near-term and long-term prospects.",
    url: "https://royalsocietypublishing.org/doi/10.1098/rspa.2017.0551",
    tags: ["quantum computing", "quantum ML", "speedup", "kernel methods"],
  },
  {
    id: "robot-learning-2023",
    title: "RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control",
    authors: "Brohan, A., Brown, N., Carbajal, J., et al. (Google DeepMind)",
    year: "2023",
    citations: 892,
    source: "CoRL",
    category: "Robotics",
    abstract:
      "We study how vision-language models trained on Internet-scale data can be incorporated directly into end-to-end robot control to boost generalization and enable emergent semantic reasoning. Our experiments suggest RT-2 demonstrates substantially better generalization and emergent capabilities compared to other baselines.",
    url: "https://arxiv.org/abs/2307.15818",
    tags: ["robotics", "vision-language", "RT-2", "control"],
  },
  {
    id: "data-science-survey-2024",
    title: "Automated Machine Learning: A Survey of Methods, Systems, and Challenges",
    authors: "He, X., Zhao, K., & Chu, X.",
    year: "2024",
    citations: 2300,
    source: "ACM Computing Surveys",
    category: "Data Science",
    abstract:
      "AutoML aims to automate the design of machine learning pipelines. We survey recent advances in neural architecture search, hyperparameter optimization, meta-learning, and data augmentation. We also identify open challenges and future directions for the field.",
    url: "https://dl.acm.org/doi/10.1145/3430562",
    tags: ["AutoML", "neural architecture search", "hyperparameter optimization", "survey"],
  },
  {
    id: "clip-2021",
    title: "Learning Transferable Visual Models From Natural Language Supervision",
    authors: "Radford, A., Kim, J. W., Hallacy, C., et al. (OpenAI)",
    year: "2021",
    citations: 19800,
    source: "ICML",
    category: "Computer Vision",
    abstract:
      "We study the behaviors of a system that learns visual representations from natural language supervision. Using a dataset of 400 million image-text pairs collected from the internet, we train CLIP which learns to predict which caption goes with which image and demonstrates impressive zero-shot transfer capabilities.",
    url: "https://arxiv.org/abs/2103.00020",
    tags: ["CLIP", "multimodal", "zero-shot", "vision-language"],
  },
];

export function getPapers(): ResearchPaper[] {
  return _papers;
}

export function getPaperById(id: string): ResearchPaper | undefined {
  return _papers.find((p) => p.id === id);
}

export function addPaper(paper: ResearchPaper): void {
  _papers = [paper, ..._papers];
}

export function generateId(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .slice(0, 40) + "-" + Date.now().toString(36);
}
