Sorted: Mirroring Human Logic via Local-First Semantic
Organization
Shriswarup Sawant,a) Kiran Tangod,b) and Vikrant Shendec)
Dept. of CSE (AI&ML), Rajarambapu Institute of Technology, Rajramnagar, Ishwarpur, Sangli, Maharashtra, India
a)Corresponding author: iamshrisawant@gmail.com
b)kiran.tangod@ritindia.edu
c)vikrant.shende@ritindia.edu
Abstract. Storage is cheap now, and we keep creating and storing loads of data. We end up with massive amounts of this data being
unorganized on our storage devices which we often term as "Digital Clutter". Organizing thousands of files by hand is tedious task
to do by hands, so people just don’t do it. Cloud AI solves this, but it forces you to upload your sensitive data records to foreign
servers you don’t control making it a huge privacy risk. We built Sorted to fix this locally, on our daily computers. Sorted builds
a "Vector Cloud" right inside the device storage and brings semantic search to personal files without sending anything over the
internet. It learns from how you organize things have organized existing data and refers to those habits for future organization.
Being a local system, it maintains our privacy while being a better system for data organization. On clean data, Sorted hit 93.9%
accuracy and more importantly, it managed 72.5% accuracy on noisy and messy data that people have to deal with on a day to
day basis.
INTRODUCTION
We download and create files more often than we sort them into a organized system for better access. Managing such
data, files and records is still a huge headache for workers who have deal with it [1]. Dragging and dropping files into
folders feels like a chore, leading to what researchers call "piling", just dumping everything into the Downloads folder
to avoid the cognitive load of organization. Eventually, this disorganization creates unease to navigate in it. Studies
also state that this behavior leads to piling of duplicate files [2], and not finding some needed file causes frustration
[3]. We call this Personal Information Management (PIM) [4].
Usually, while storing files, we rely on remembering where we have stored them. [5], but the need to remember is
different across different devices and systems [6]. Today, most tools in such systems for file organization require cloud
based solution to be effective. In such cases personal information needs to be protected [7], just anonymization does
not help maintain privacy of the individual [8]. Personal Information Management Systems are starting to focus on
local processing [9] and Sorted balances convenience and privacy by running entirely on device without any offload
to cloud. It scans the user’s organization of files and learns to mimic those habits and logic rather than forcing files
into rigid, pre-made categories.
SYSTEM DESIGN
Sorted as a system has three main stages: watch, understand, match. It uses a Real-Time Watcher daemon monitoring
events, a Context Extractor, and a Vector Cloud Inference Engine.
Watching the File System
To keep the organization automated without any disturbance to user, we wrote a background daemon using the
watchdog library to watch folders like Downloads for file creation events. To avoid corrupting newly created files the
system takes access only when OS is done with manipulation of file, also ignoring junk files like .tmp files to save
battery.
FIGURE 1. Architecture Overview. Figure 1 illustrates the event-driven pipeline of the Watcher. Initially the entire system is kept
inactive to conserve resources until triggered by the Watcher, at which point the system extracts structural proxies (Header/Footer)
and maps the file against the local index made of organized files.
Context Extraction & Semantic Embedding
Running a massive Transformer model on daily devices would overwhelm the device resources. Thus we use small
architectures like MiniBERT which act like Siamese networks but are super lightweight [16]. To save even more
resources, we compress the vectors of extracted and indexed data using the Maximum Coding Rate Reduction (MCR2)
protocol, reducing the vectors by 50 to 70% [17]. This way, the system gets a dense index without taking up significant
amount of storage. Usually the main intent of information lies the leading and trailing portion of document. Thus, we
don’t read the whole document, we just use the first and last 500 characters for semantics and classification of file.
The Vector Cloud (Memory)
Most classifiers average a folder’s files into one vector which fails for personal information folders [15]. For example,
a "Finance" folder may have spreadsheets, receipts, and tax forms. Averaging them would make mess by not recognizing the individual data inside that folder. Sorted indexes every single file as a unique dot, making a Vector Cloud
and this way, it remembers specific files, like recognizing a specific power bill—instead of relying on a inappropriate
folder average. We use contrastive learning to keep these data points separated by meaning [13].
Making the Decision (Inference)
When a new file is created and detected by watcher, through Sorted, it’s vector gets projected in vector cloud index to
find it’s neighbours by meaning. We use a Rank-Weighted Score for candidate folder F calculated as:
ScoreF = ∑
d∈Nk∩F
Sim(q,d)
Rankd
(1)
The system avoids making any mistakes based on a majority vote from weak matches by assigning the most weight
to folder ranking 1. Most files created by user have some directory to organize into. However those created with
completely new contents cannot be associated into existing directory if intent is does not match. In such cases relying
on only the semantic spaces would not help in inference to sort file effectively [18]. So we introduced “Confidence
Gate” at 0.5 score as a threshold. If the best match folder score is lower than that, Sorted just keeps the file as
Unsorted.
When the new files are moved by automation or manually, online learning is used to update the vector index without
a repeat look at the complete file system. In a real file system, there is an established hierarchy among files and folders
within directories. Sorted uses a Depth Bias for when a file matches a root folder and a sub-folder equally, it gives a
bias to the sub-folder for a more specific sort.
EVALUATION
To test the system with harsh data, we created a synthetic dataset of documents that mimic the noise and semantics of
those we have to manage.Sorted was compared to TF-IDF, Naive Bayes, and Centroid AI based methods of document
classification which are commonly used in most such automations.
FIGURE 2. Robustness: Most methods work fine on clean dataset (Phase B), but sorted stands out because it keeps working even
when the documents are messy (Phase A).
The "Torture Test" (Phase A)
In this test, we compared the classification methods by classification against different documents in a synthetic dataset
that would mimic digital clutter that accumulates on the device. As Table 1 shows, the Centroid based method had a
drop in accuracy to 52.8%, while Sorted delivered an accuracy of 72.5% as it indexes individual files.
TABLE 1. Performance Under Noise (Phase A)
System Accuracy Latency F1-Score
TF-IDF 40.3% 1.97 ms 0.392
Naive Bayes 48.1% 1.44 ms 0.426
Centroid Baseline 52.8% 24.29 ms 0.507
Sorted (Ours) 72.5% 28.36 ms 0.716
FIGURE 3. Latency: Sorted delivers a better accuracy with lesser latency.
The Academic Benchmark (Phase B)
We also evaluated Sorted against various methods with the 20 Newsgroups dataset to make sure that we did not ruin
performance under normal conditions. Sorted can organize a file in about 58 ms, making the task of file organization
instant without any effort or cognitive load (Table 2).
TABLE 2. Clean Benchmark Performance (Phase B)
System Accuracy Latency F1-Score
TF-IDF 79.9% 13.00 ms 0.798
Naive Bayes 91.3% 4.09 ms 0.913
Centroid Baseline 91.8% 66.53 ms 0.921
Sorted (Ours) 93.9% 58.47 ms 0.939
DISCUSSION
First test show why older tools fail, averaging a intent folder assumes everything inside is identical, which is in general
not. Sorted’s Vector Cloud fixes this by treating every document as an individual. The accuracy and speed shows that
we do not need to read the whole document to effectively organized it. Just reading the outer leading and trailing
characters is enough to sort the documents right where they would belong with human intent. Having MiniBERT
setup on local device, MCR2 compression we do not compromise any local resources while maintaining privacy
regarding data.
CONCLUSION
Sorting documents into dedicated folders has been a tedious thing to do and we often let all files get piled up and get
frustrated. Sorted fixes this piling problem by learning and copying our file organization habits and logic. It keeps
the device clean, neat and organized, free of any digital clutter avoiding any cloud based solutions that would ruin our
privacy.
REFERENCES
1. J. D. Dinneen and C. A. Julien, “The ubiquitous digital file: a review of file management research,” J. Assoc. Inf. Sci. Technol., vol. 71, no. 1,
pp. E1–E32, 2020.
2. J. D. Dinneen and C.-A. Julien, “What’s in People’s Digital File Collections?” in Proc. 82nd Annu. Meeting Assoc. Inf. Sci. Technol. (ASIS&T
’19), 2019, p. 56.
3. M. Balogh, “Taming the paper pile at home: Adopting Personal Electronic Records,” arXiv preprint arXiv:2204.13282, 2022.
4. W. Jones, J. D. Dinneen, R. Capra, A. R. Diekema, and M. A. Pérez-Quiñones, “Personal Information Management,” in Encyclopedia of
Library and Information Science, 4th ed., M. Levine-Clark and J. McDonald, Eds. New York, NY: Taylor & Francis, 2017, pp. 3584–3605.
5. D. Barreau and B. A. Nardi, “Finding and Reminding File Organization from the Desktop,” SIGCHI Bull., vol. 27, no. 3, p. 39, 1995.
6. J. D. Dinneen and I. Frissen, “Mac Users Do It Differently: the Role of Operating System and Individual Differences in File Management,” in
Ext. Abstr. 2020 CHI Conf. Human Factors Comput. Syst. (CHI EA ’20), 2020.
7. S. S. Al-Fedaghi and B. Thalheim, “Personal Information Databases,” Int. J. Comput. Sci. Inf. Secur., vol. 5, no. 1, 2009.
8. S. Al-Fedaghi, “Privacy Things: Systematic Approach to Privacy and Personal Identifiable Information,” 2018.
9. H. Janssen and J. Singh, “Personal Information Management Systems,” Internet Policy Rev., vol. 11, no. 2, 2022.
10. N. Reimers and I. Gurevych, “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,” in Proc. 2019 Conf. Empirical Methods
Natural Lang. Process. and 9th Int. Joint Conf. Natural Lang. Process., 2019.
11. J. Hillebrand, “The Best of BERT Worlds: Improving minBERT with multi-task extensions,” Stanford Univ., Tech. Rep., 2022.
12. Q. Peng, D. Weir, and J. Weeds, “Structure-aware Sentence Encoder in BERT-Based Siamese Network,” in Proc. 6th Workshop Representation
Learning for NLP (RepL4NLP-2021), 2021.
13. H. Kiyomaru and S. Kurohashi, “Contextualized and Generalized Sentence Representations by Contrastive Self-Supervised Learning: A Case
Study on Discourse Relation Analysis,” in Proc. 2021 Conf. NAACL: HLT, 2021.
14. H. Tan, W. Shao, H. Wu, K. Yang, and L. Song, “A Sentence is Worth 128 Pseudo Tokens: A Semantic-Aware Contrastive Learning Framework
for Sentence Embeddings,” in Findings Assoc. Comput. Linguistics: ACL 2022, 2022.
15. M. Bendersky, D. Metzler, M. Najork, and X. Wang, “Searching Personal Collections,” in Information Retrieval: Advanced Topics and
Techniques, O. Alonzo and R. Baeza-Yates, Eds. ACM Press, 2025, ch. 14.
16. G. J. Sufleta II, “Integrating Cosine Similarity into minBERT for Paraphrase and Semantic Analysis,” Stanford Univ., Tech. Rep., 2022.
17. D. Ševerdija, T. Prusina, A. Jovanovic, L. Borozan, J. Maltar, and D. Matijevi ´ c, “Compressing Sentence Representation with Maximum Coding ´
Rate Reduction,” arXiv preprint arXiv:2304.12674, 2023.
18. C. Min, Y. Chu, L. Yang, B. Xu, and H. Lin, “Locality Preserving Sentence Encoding,” in Findings Assoc. Comput. Linguistics: EMNLP 2021,
2021.