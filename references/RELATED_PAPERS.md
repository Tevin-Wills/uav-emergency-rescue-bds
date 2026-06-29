# Related Papers — BDS-SMC2 (verified 2026-06-23)

Curated, **verified** references closest to the BDS-SMC2 methodology
(BeiDou-3 short-message communication · rescue payload encoding · delivery
reliability / latency · UAV search-and-rescue integration).

Legend: ✅ PDF downloaded to this folder · 🔗 verified online, manual download
(paywalled or bot-blocked).

---

## Downloaded to this folder (2 PDFs)

### ✅ 1. BeiDou Short-Message Satellite Resource Allocation (Deep RL)
`Entropy_2021_BeiDou_SMC_ResourceAllocation_DRL.pdf`
- *Entropy* (MDPI), 2021, **23(8):932**. Open access. PMC8392218.
- URL: https://www.mdpi.com/1099-4300/23/8/932 · doi:10.3390/e23080932
- **Why relevant:** models the BeiDou short-message satellite *resource/capacity*
  allocation problem — supports your capacity-limit (⟦CAPACITY-CHECK⟧) and
  rate-limit framing in Paper 1 §II.A and Paper 2 (survivors-per-minute).

### ✅ 2. Resilient Communication Infrastructure in Disaster Relief (→ Paper 1 [REF-1])
`arXiv_2024_DisasterReliefComms.pdf`
- "Solutions for Sustainable and Resilient Communication Infrastructure in
  Disaster Relief and Management Scenarios," arXiv:2410.13977, 2024. Open access.
- URL: https://arxiv.org/abs/2410.13977
- **Why relevant:** documents cellular/base-station failure after the Feb 2023
  Türkiye earthquakes (up to ~60% of network down; 2,451/8,900 base stations
  offline) — a citable source for your **[REF-1]** "disaster comms failure"
  motivation (Paper 1 §I). Companion: arXiv:2409.06822 "Five Key Enablers for
  Communication during and after Disasters."

---

## Cite-only (verified online; download manually)

### 🔗 A. Requirement-Oriented TT&C Method for Satellite Based on BDS-3 SMC  ★ closest on latency
- *Space: Science & Technology*, 2022, article **0038**. Open access.
- URL / PDF: https://spj.science.org/doi/10.34133/space.0038 · doi:10.34133/space.0038
- **Why relevant (high value):** gives the BeiDou-SMC **latency reference points**
  you frame against — **RSMC response delay ≤ 1 s**; **GSMC latency < 15 s (95%, 2σ)**.
  Use directly in Paper 1 §V (latency) and revision-note **L2**. Download by hand:
  open the URL → "PDF/EPUB" (the site serves a JS page that blocks `curl`).

### 🔗 B. Urban Emergency Picture Transmission Mechanism Based on Beidou Short Message  ← your [REF-6]
- IEEE Xplore, document **10019970** (conf., ~2022/23). Paywalled.
- URL: https://ieeexplore.ieee.org/document/10019970/
- **Why relevant:** BeiDou-SMC for *emergency* data delivery where the message
  terminates at a human operator — exactly the prior-art you contrast with your
  autonomous UAV trigger (Paper 1 §II.D). **This resolves your [REF-6] placeholder.**

### 🔗 C. Design of BeiDou-based Multimode Communication Maritime SAR Terminal  ← UAV/SAR neighbour
- IEEE Xplore, document **10426479** (conf., ~2023/24). Paywalled.
- URL: https://ieeexplore.ieee.org/document/10426479/
- **Why relevant:** closest IEEE *search-and-rescue terminal* using BeiDou
  communication; supports Paper 1 §II.D and Paper 2 §3 (UAV+BeiDou SAR, human-terminated).

### 🔗 D. Introduction to global short message communication service of BeiDou-3  ★ anchor
- Li G. et al., *Advances in Space Research*, 2021, **67(5):1701–1708**. Paywalled.
- URL: https://www.sciencedirect.com/science/article/abs/pii/S027311772030867X
  · doi:10.1016/j.asr.2020.12.011
- **Why relevant:** your primary anchor [R1]. GSMC architecture incl. an
  **emergency SAR** subtype; 2149-TX, 97.72% aggregate delivery — the result you
  position against with environment-stratified, application-layer data.

### 🔗 E. GNSS real-time PPP with BDS-3 global short-message devices
- *GPS Solutions*, 2022. Paywalled. doi via ScienceDirect S0273117722003453.
- URL: https://www.sciencedirect.com/science/article/abs/pii/S0273117722003453
- **Why relevant:** RTK/PPP *over* BeiDou SMC — the "broadcast corrections" prior
  art that your Paper 2 §3 inverts (you send the *survivor's* RTK-corrected position).

---

## BibTeX (verified entries)

```bibtex
@article{li2021bds3gsmc,
  title   = {Introduction to global short message communication service of
             BeiDou-3 navigation satellite system},
  author  = {Li, Guangcai and others},
  journal = {Advances in Space Research},
  volume  = {67}, number = {5}, pages = {1701--1708}, year = {2021},
  doi     = {10.1016/j.asr.2020.12.011}
}

@article{spj2022bds3ttc,
  title   = {Requirement-Oriented {TT\&C} Method for Satellite Based on
             {BDS-3} Short-Message Communication System},
  journal = {Space: Science \& Technology},
  year    = {2022}, articleno = {0038}, doi = {10.34133/space.0038}
}

@article{entropy2021bdssmcdrl,
  title   = {{BeiDou} Short-Message Satellite Resource Allocation Algorithm
             Based on Deep Reinforcement Learning},
  journal = {Entropy}, volume = {23}, number = {8}, pages = {932},
  year    = {2021}, doi = {10.3390/e23080932}
}

@inproceedings{ieee2023urbanpicbds,
  title     = {Urban Emergency Picture Transmission Mechanism Based on
               Beidou Short Message},
  booktitle = {Proc. IEEE Conf.}, year = {2022},
  note      = {IEEE Xplore document 10019970}
}

@inproceedings{ieee2024maritimesar,
  title     = {Design of {BeiDou}-based Multimode Communication Maritime
               Search and Rescue Terminal},
  booktitle = {Proc. IEEE Conf.}, year = {2023},
  note      = {IEEE Xplore document 10426479}
}

@misc{arxiv2024disastercomms,
  title  = {Solutions for Sustainable and Resilient Communication
            Infrastructure in Disaster Relief and Management Scenarios},
  year   = {2024}, eprint = {2410.13977}, archivePrefix = {arXiv}
}
```

> Note: a few fields (full author lists, exact conference names/years for the
> two IEEE Xplore items) still need confirmation from the official record before
> submission — they are flagged in `note=`.
