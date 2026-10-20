// Script of the guide pages. The text is plain HTML (so search engines read it);
// this only adds the mini trainer where a page has <div class="mini-trainer-slot" data-kind="..." data-lang="...">.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../index.css'
import './landing.css'
import MiniTrainer from './MiniTrainer.jsx'

for (const slot of document.querySelectorAll('.mini-trainer-slot')) {
  createRoot(slot).render(
    <StrictMode>
      <MiniTrainer kind={slot.dataset.kind} lang={slot.dataset.lang} />
    </StrictMode>,
  )
}
