**data**
- data_zhou.xlsx
    - datasets from Zhou, S. et al. (2025). A general physics-informed neural network framework for fatigue life prediction of metallic materials. Engineering Fracture Mechanics, 322, 111136.
- data_zhou.ipynb
    - data cleaning and exploration of Zhou

**models**
- **paris**
    - *workflow.ipynb*
        - contains:
            - generated inputs
            - volume, defect density, PDF
            - max defects
    -   *workflow_2.ipynb*
        - current working directory
        - generates synthetic data from VED
        - notes, variable, equation, function lists, and citations: [https://docs.google.com/document/d/1CRuVP2ta7WAxRMIw37ggpHAKsiX_LRi3ehZopM3fYvU/edit?usp=sharing]
    - graphs
        - folder containing all graphs from workflow.ipynb
    - inputs.py
        - inputs manipulation
        - same as workflow.ipynb
        - easier to reference later in other notebooks
    - density.py
        - volume, defect density, PDF
        - same as workflow.ipynb
        - easier to reference later in other notebooks

- **basquin**
    - deterministic.ipynb
        - deterministic model 
        - predicts a single fatigue life for a given defect and stress using Basquin’s law
        - S-N, Shozawa curves
    - probabilistic.ipynb
        - probabilistic model
        - predicts a distribution of fatigue lives using Basquin’s law
        - PDFs, GEV, S-N, Shiozawa, reliability curves under fixed and varying stress levels
    - probabilistic_ved.ipynb
        - probabilistic model using the defect density and VED as a process input that controls defect statistics
        - predicts a distribution of fatigue lives using Basquin’s law
        - PDFs, GEV, S-N, Shiozawa, reliability curves under fixed and varying stress levels

**practice**
- shiozawa.ipynb
    - the first deterministic/probabilistic model
- practice.ipynb
    - neural network basics
- practice_parislaw.ipynb
    - neural network basics with the Paris law

