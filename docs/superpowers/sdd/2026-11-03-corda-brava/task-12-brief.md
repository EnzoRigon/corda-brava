### Task 12: Assets — copy owner sprites + crests + Mascot/Crest components

**Files:**
- Copy (verbatim, via shell): `docs/mascot-references/mascot-test/assets/{saci,mosq}_*.{gif,png}` → `frontend/src/assets/mascots/`; `docs/logo-references/{inter,gremio}.png` → `frontend/src/assets/crests/`
- Create: `frontend/src/components/Mascot.tsx`, `frontend/src/components/Crest.tsx`
- Test: `frontend/src/components/Mascot.test.tsx`

**Interfaces:**
- Produces: `<Mascot team state />` where `state ∈ idle|straining|winning|losing|happy|crying` maps to the owner sprites (idle→`*_master.png`, straining→`*_pull.gif`, winning/happy→`*_happy.gif`, losing→`*_defeat.gif`, crying→`*_cry.gif`); `image-rendering:pixelated`; Grêmio mirrored to face center. `<Crest team />` renders the copied crest png. **No drawing of characters in code — assets are imported files.**

- [ ] **Step 1:** Write `Mascot.test.tsx`: for `team=INTER state=straining` the rendered `<img>` src includes `saci_pull`; `team=GREMIO state=happy` includes `mosq_happy`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Copy assets with `cp`; implement components importing them.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(frontend): copy owner mascot/crest assets + Mascot/Crest components`.

