-- Seed REF_CONTROLLED_DRUGS with representative NDCs across DEA Schedule II-V
-- and commonly abused drug classes

INSERT INTO network_graph.ref_controlled_drugs (ndc, drug_name, drug_class, dea_schedule, is_controlled, is_commonly_abused) VALUES
-- Schedule II Opioids
('00406-0220-62', 'Oxycodone HCl 5mg', 'opioids', 'II', TRUE, TRUE),
('00406-0222-62', 'Oxycodone HCl 10mg', 'opioids', 'II', TRUE, TRUE),
('00406-0224-62', 'Oxycodone HCl 15mg', 'opioids', 'II', TRUE, TRUE),
('00406-0226-62', 'Oxycodone HCl 20mg', 'opioids', 'II', TRUE, TRUE),
('00591-0405-01', 'Oxycodone HCl 30mg', 'opioids', 'II', TRUE, TRUE),
('00228-2898-11', 'OxyContin 10mg ER', 'opioids', 'II', TRUE, TRUE),
('00228-2899-11', 'OxyContin 20mg ER', 'opioids', 'II', TRUE, TRUE),
('00228-2900-11', 'OxyContin 40mg ER', 'opioids', 'II', TRUE, TRUE),
('00406-1220-62', 'Hydromorphone 2mg', 'opioids', 'II', TRUE, TRUE),
('00406-1222-62', 'Hydromorphone 4mg', 'opioids', 'II', TRUE, TRUE),
('00406-1224-62', 'Hydromorphone 8mg', 'opioids', 'II', TRUE, TRUE),
('00591-3535-01', 'Morphine Sulfate 15mg', 'opioids', 'II', TRUE, TRUE),
('00591-3536-01', 'Morphine Sulfate 30mg', 'opioids', 'II', TRUE, TRUE),
('00591-2830-01', 'Fentanyl 25mcg/hr Patch', 'opioids', 'II', TRUE, TRUE),
('00591-2831-01', 'Fentanyl 50mcg/hr Patch', 'opioids', 'II', TRUE, TRUE),
('63481-0623-70', 'Hydrocodone-APAP 5/325mg', 'opioids', 'II', TRUE, TRUE),
('63481-0624-70', 'Hydrocodone-APAP 7.5/325mg', 'opioids', 'II', TRUE, TRUE),
('63481-0625-70', 'Hydrocodone-APAP 10/325mg', 'opioids', 'II', TRUE, TRUE),
('00406-0367-62', 'Methadone 5mg', 'opioids', 'II', TRUE, TRUE),
('00406-0368-62', 'Methadone 10mg', 'opioids', 'II', TRUE, TRUE),

-- Schedule II Stimulants
('00555-0764-02', 'Amphetamine Salts 10mg', 'stimulants', 'II', TRUE, TRUE),
('00555-0766-02', 'Amphetamine Salts 20mg', 'stimulants', 'II', TRUE, TRUE),
('00555-0768-02', 'Amphetamine Salts 30mg', 'stimulants', 'II', TRUE, TRUE),
('57844-0110-01', 'Adderall XR 10mg', 'stimulants', 'II', TRUE, TRUE),
('57844-0120-01', 'Adderall XR 20mg', 'stimulants', 'II', TRUE, TRUE),
('57844-0130-01', 'Adderall XR 30mg', 'stimulants', 'II', TRUE, TRUE),
('00406-1010-01', 'Methylphenidate 10mg', 'stimulants', 'II', TRUE, TRUE),
('00406-1020-01', 'Methylphenidate 20mg', 'stimulants', 'II', TRUE, TRUE),
('21695-0208-30', 'Concerta 18mg ER', 'stimulants', 'II', TRUE, TRUE),
('21695-0209-30', 'Concerta 36mg ER', 'stimulants', 'II', TRUE, TRUE),

-- Schedule IV Benzodiazepines
('00228-2057-11', 'Alprazolam 0.25mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00228-2058-11', 'Alprazolam 0.5mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00228-2059-11', 'Alprazolam 1mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00228-2060-11', 'Alprazolam 2mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00781-1064-01', 'Lorazepam 0.5mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00781-1065-01', 'Lorazepam 1mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00781-1066-01', 'Lorazepam 2mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00093-8108-01', 'Diazepam 5mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00093-8109-01', 'Diazepam 10mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00093-5340-01', 'Clonazepam 0.5mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00093-5341-01', 'Clonazepam 1mg', 'benzodiazepines', 'IV', TRUE, TRUE),
('00093-5342-01', 'Clonazepam 2mg', 'benzodiazepines', 'IV', TRUE, TRUE),

-- Gabapentinoids (Schedule V in some states, commonly abused)
('27241-0050-05', 'Gabapentin 100mg', 'gabapentinoids', 'V', TRUE, TRUE),
('27241-0051-05', 'Gabapentin 300mg', 'gabapentinoids', 'V', TRUE, TRUE),
('27241-0052-05', 'Gabapentin 400mg', 'gabapentinoids', 'V', TRUE, TRUE),
('27241-0053-05', 'Gabapentin 600mg', 'gabapentinoids', 'V', TRUE, TRUE),
('27241-0054-05', 'Gabapentin 800mg', 'gabapentinoids', 'V', TRUE, TRUE),
('00071-1013-68', 'Pregabalin (Lyrica) 50mg', 'gabapentinoids', 'V', TRUE, TRUE),
('00071-1014-68', 'Pregabalin (Lyrica) 75mg', 'gabapentinoids', 'V', TRUE, TRUE),
('00071-1015-68', 'Pregabalin (Lyrica) 150mg', 'gabapentinoids', 'V', TRUE, TRUE),
('00071-1016-68', 'Pregabalin (Lyrica) 300mg', 'gabapentinoids', 'V', TRUE, TRUE),

-- Muscle Relaxants (commonly abused, not all scheduled)
('00228-2100-11', 'Carisoprodol (Soma) 250mg', 'muscle_relaxants', 'IV', TRUE, TRUE),
('00228-2101-11', 'Carisoprodol (Soma) 350mg', 'muscle_relaxants', 'IV', TRUE, TRUE),
('00591-5513-01', 'Cyclobenzaprine 5mg', 'muscle_relaxants', 'NONE', FALSE, TRUE),
('00591-5514-01', 'Cyclobenzaprine 10mg', 'muscle_relaxants', 'NONE', FALSE, TRUE),

-- Schedule III
('12496-1206-01', 'Buprenorphine-Naloxone 8/2mg', 'opioids', 'III', TRUE, TRUE),
('12496-1208-01', 'Buprenorphine-Naloxone 2/0.5mg', 'opioids', 'III', TRUE, TRUE),
('00555-0901-02', 'Testosterone Cypionate 200mg/mL', 'anabolic_steroids', 'III', TRUE, FALSE),

-- Schedule IV (additional)
('00093-0089-01', 'Zolpidem (Ambien) 5mg', 'sedatives', 'IV', TRUE, TRUE),
('00093-0090-01', 'Zolpidem (Ambien) 10mg', 'sedatives', 'IV', TRUE, TRUE),
('00093-5250-01', 'Tramadol 50mg', 'opioids', 'IV', TRUE, TRUE)
ON CONFLICT DO NOTHING;
