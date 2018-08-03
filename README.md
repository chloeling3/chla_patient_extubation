# Personalized Predictions of Patient Physiologies for Successful Extubation Using Neural Networks
The methods for predicting extubation success in critically ill children vary among individuals and institutions. Extubation readiness is a subjective assessment based on clinical evaluation of vital signs, lab values, and perceived requirement of ventilatory support. This study defined extubation readiness based on the physiologic state associated with successful extubations and developed a Recurrent Neural Network (RNN) to predict these physiologic states in individual patients.

### Methods 
A retrospective study was conducted using EMR from patients admitted to the PICU at Children’s Hospital of Los Angeles (CHLA) from 2009-2017. 1985 episodes were selected where patients were intubated for at least 12 hours, extubated without reintubation within 24 hours, and survived their PICU episode. Each episode contained 365 charted vitals, labs, interventions, and drugs during their PICU episode. The physiologic state associated with successful extubation was defined as the mean heart rate, systolic blood pressure, diastolic blood pressure, respiratory rate, and serum bicarbonate in the 6 hour window prior to extubation. An RNN was trained on all available variables prior to extubation to predict this state up to 6 hours prior to extubation and compared to age-normal values.

### Results 
The mean absolute error for RNN predictions were compared to age-normal values. Heart rate was 16.0 vs 20.0 bpm, systolic blood pressure was 9.3 vs 11.0 mmHg, diastolic blood pressure was 9.2 vs 10.6 mmHg, respiratory rate was 5.0 vs 7.1 bpm, serum bicarbonate was 3.2 vs 3.8 mg/dL. 

<img width="933" alt="model 1" src="https://user-images.githubusercontent.com/31297724/43617255-d7dbf1f0-9675-11e8-9555-365ebd2eb731.png"> 

<img width="677" alt="model 2" src="https://user-images.githubusercontent.com/31297724/43617276-f400810c-9675-11e8-8c53-5357ba8008f3.png">

<img width="695" alt="model 3" src="https://user-images.githubusercontent.com/31297724/43617280-f593487e-9675-11e8-9496-077b37fbe898.png">


### Conclusion
The RNN model better approximates patient-specific physiologic states for successful extubation. Such a model can improve current extubation practice by personalizing assessments for extubation readiness, reducing complications associated with unsuccessful extubations.

