---
title: Hypertension and Mental Health in U.S. Adults
emoji: 🫀
colorFrom: red
colorTo: blue
sdk: docker
app_file: app.py
pinned: false
---

<!-- Hugging Face Space configuration above — required for deployment -->

# Hypertension and Mental Health in U.S. Adults

An interactive public health dashboard exploring how mental health outcomes differ between adults with and without hypertension across the United States.

## Live Dashboard

> 🔗 [View on Hugging Face Spaces](https://huggingface.co/spaces/ashleysofiaalfaro/hypertension-mental-health)

*Note: If there has been a period of inactivity, there is a possibility the space is "sleeping," which causes a loading delay.*

## Built With

[![Visual-Studio][vs-code-shield]]
[![Jupyter-Notebook][jupyter-shield]]
[![Python][python-shield]]
[![Plotly-Dash][plotly-dash-shield]]

---

## Background

Hypertension, or high blood pressure, is one of the most prevalent chronic condition in the United States. According to the CDC, nearly 48% of U.S. adults had hypertension between 2021 and 2023. Beyond increasing the risk of other cardiovascular diseases, hypertension carries psychosocial consequences that are less frequently examined at the population level. Research suggests that adults with hypertension experience elevated rates of depression and poor mental health compared to those without the condition. For example, a CDC-affiliated study found that depressive symptoms were significantly associated with hypertension prevalence and treatment among U.S. adults, suggesting that mental health status may influence how individuals manage their blood pressure (Fang et al., 2022).

However, findings across the literature are **mixed**. While some evidence points to hypertension increasing the risk of depression through physiological stress pathways, others suggest that depression may itself contribute to hypertension through behavioral and homronal mechanisms (Comorbidity of Anxiety and Depression With Hypertension, 2024). 

Despite growing interest in this relationship, there remains a gap in accessible, population-level tools that allow users to explore how mental health burden differs between hypertensive and non-hypertensive adults across demographic and geographic subgroups. This dashboard aims to address that gap.

### Research Questions
**Primary:** How does mental health differ between adults with and without hypertension?
 
**Secondary:**
- Which states show the highest burden of poor mental health among adults with hypertension, and does this pattern differ from adults without hypertension?
- Among adults with hypertension, which demographic groups report the highest prevalence of depression and frequent mental distress?

---

## Data

This dashboard uses data from the **CDC Behavioral Risk Factor Surveillance System
(BRFSS)**, the nation's premier system of health-related telephone surveys collecting
state-level data about U.S. residents' health behaviors, chronic conditions, and use of
preventive services.

- **Survey years used:** 2015, 2017, 2019, 2021, 2023
- **Approximate sample size:** ~400,000 respondents per year across all 50 states,
  the District of Columbia, and U.S. territories
- **Survey weights:** All prevalence estimates are weighted using BRFSS survey weights
  (`LLCPWT`) to produce population-representative estimates at the national and
  state level

### Key Variables

| Variable | Description |
|---|---|
| `High_BP` | Ever told by a health professional they have high blood pressure |
| `Depression` | Ever told by a health professional they have a depressive disorder |
| `Mental_Hlth` | Number of days in the past 30 days mental health was not good |
| `Race` | Race/ethnicity of respondent |
| `Age` | Age group of respondent |
| `Sex` | Sex of respondent |

### Data Access

BRFSS data is publicly available through the CDC:
[https://www.cdc.gov/brfss/](https://www.cdc.gov/brfss/)

---

## Findings
1. Adults with hypertension reported higher rates of depression and frequent mental distress compared to adults without hypertension.
2. Younger adults (18-24, 25-29) with hypertension consistently had the highest rates for poor mental health. A similiar age pattern appeared for adults without hypertension, however, the prevalence rates were lower in comparison. 
3. Multiracial and American Indian/Alaska Native adults reported the highest rates for depression and frequent mental distress regardless of hypertension status. This suggests that there are factors beyond hypertension that is contributing to the mental health disparities.

---

## Future Directions

- Include socioeconomic factors and see what patterns emerge between adults with and without hypertension.
- Explore how mental health and hypertension affect other cardiovascular outcomes.
- Investigate resource availability, such as hospitals and mental health centers.
- Use statisical modeling (e.g., logistic regression) to better understand how strongly hypertension is associated with poor mental health.

---

## Acknowledgements

This project was developed as part of the **SCIPE CI-SIP (Cyberinfrastructure Summer Internship Program)** in collaboration with the **Hawaiʻi Data Science Institute (HiDSI)**.

**Mentors:**
- Andrew Zilnicki
- Haohan Yuan

**CI-SIP 2026**
- Dr. Alex Stokes
- SCIPE Program
- Hawaii Data Science Institute

**Project Support**
- Dr. Sean Cleveland 
- NSF Award #2417946

---

## References

- Centers for Disease Control and Prevention. (2024). *High blood pressure facts.*
  https://www.cdc.gov/high-blood-pressure/data-research/facts-stats/index.html
  
- Fang, J., et al. (2022). Association of depressive symptoms and hypertension
  prevalence, awareness, treatment and control among US adults. *Journal of
  Hypertension, 40*(9), 1658–1665.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11139467/


  <!-- TECH BADGES -->
[vs-code-shield]: https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white
[python-shield]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[plotly-dash-shield]: https://img.shields.io/badge/plotly-3F4F75.svg?style=for-the-badge&logo=plotly&logoColor=white
[jupyter-shield]: https://img.shields.io/badge/jupyter-%23FA0F00.svg?style=for-the-badge&logo=jupyter&logoColor=white