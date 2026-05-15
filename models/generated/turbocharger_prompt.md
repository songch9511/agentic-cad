Generate a K26/K27-style turbocharger assembly from the exploded service diagram reference. Use millimeters. Build editable B-rep CAD solids, not mesh-only geometry. The output must include both a properly assembled turbocharger STEP and a service-exploded STEP with the parts arranged in the same logical order as the reference image.

Core design:
- Product: automotive turbocharger, K26/K27 rebuild-diagram style
- Coordinate system: X axis is the rotor/shaft axis, negative X is compressor/cold side, positive X is turbine/hot side
- Overall style: manufacturable cast/forged turbocharger hardware, suitable for AI-generated CAD demo footage
- Geometry style: robust simplified solids, not over-detailed internals
- Materials to imply visually: cast aluminum compressor housing, darker cast iron turbine housing, steel shaft, seals, rings, clips, retainers, and bolts

Required legend parts:
- A. Seal plate
- B. Compressor wheel / inducer
- C. Compressor housing, cold side
- D. Bearing housing / CHRA
- E. Heat shield
- F. Turbine wheel and shaft / exducer
- G. Turbine housing, hot side
- 1. Journal bearings, two instances
- 2. Bearing clips, four instances
- 3. Thrust washer
- 4. Thrust bearing
- 5. Oil splash guard / thrust bearing retainer
- 6. Spacer
- 7. Mating ring
- 8. Compressor seal
- 9. Compressor housing O-ring
- 10. Seal plate O-ring
- 11. Seal plate bolts, six instances
- 12. Compressor housing bolts, six instances
- 13. Compressor housing retainers, three instances
- 14. Turbine seals, two instances
- 15. Turbine housing bolts, six instances
- 16. Turbine housing retainer / lock tabs, three instances
- 17. Compressor nut

Assembly requirements:
- Keep A-G and 1-17 as separate CAD components or separate B-rep solids.
- Align the rotating group coaxially: compressor nut, compressor wheel, seal stack, journal bearings, shaft, heat shield, turbine seals, and turbine wheel must share the X-axis.
- Place compressor housing C around compressor wheel B and seal plate A.
- Place bearing housing D between compressor side and turbine side, with top oil feed and bottom oil drain details.
- Place heat shield E between bearing housing D and turbine housing G.
- Place turbine housing G around the turbine wheel end of F.
- Place housing bolts, retainers, clips, seals, O-rings, and lock tabs where they correspond to the reference diagram.
- Export a compact assembled model and a readable exploded service-layout model.

Validation:
- Report 7 major legend parts A-G.
- Report 17 service legend part categories 1-17.
- Report rebuild-kit categories 1, 2, 4, 8, 9, 10, 14, and 17.
- Verify the rotor stack is coaxial.
- Verify external compressor/turbine ports, oil feed, and oil drain are present.
- Report assembled and exploded bounding boxes.
