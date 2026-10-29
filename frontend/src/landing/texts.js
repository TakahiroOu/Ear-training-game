// Texts of the mini trainers on the guide pages (the page texts themselves are in the HTML files).
export default {
  ja: {
    instructions: {
      interval: '2つの音が一音ずつ、次に同時に鳴ります。音程（インターバル）の名前を選んでください。',
      chord: '3つの音が同時に鳴ります。和音の種類を選んでください。',
      degree: '最初に基準の「ド」、次にハ長調の音が鳴ります。2つめの音を選んでください。',
      pitch: '基準の音なしで、白鍵の音が1つ鳴ります。何の音か当ててください。',
    },
    start: '▶ 問題を聴く',
    newQuestion: '別の問題',
    next: '次の問題',
    loading: '音を読み込み中…',
    replay: 'もう一度聴く',
    score: (right, asked) => `${asked}問中 ${right}問正解`,
    right: '正解！',
    wrong: (answer) => `残念！正解は「${answer}」です。`,
    openApp: 'アプリでもっと練習する（無料）',
    names: {
      interval: {
        m2: '短2度', M2: '長2度', m3: '短3度', M3: '長3度', P4: '完全4度', P5: '完全5度', M6: '長6度', P8: 'オクターブ',
      },
      chord: { major: '長三和音', minor: '短三和音', diminished: '減三和音', augmented: '増三和音' },
      degree: { do: 'ド', re: 'レ', mi: 'ミ', fa: 'ファ', so: 'ソ', la: 'ラ', ti: 'シ' },
      pitch: { do: 'ド', re: 'レ', mi: 'ミ', fa: 'ファ', so: 'ソ', la: 'ラ', ti: 'シ' },
    },
  },
  en: {
    instructions: {
      interval: 'Two notes play one after the other, then together. Choose the interval.',
      chord: 'Three notes play together. Choose the type of triad.',
      degree: 'First you hear C (do), then another note of C major. Choose the second note.',
      pitch: 'One white-key note plays, with no reference note. Which note is it?',
    },
    start: '▶ Play a question',
    newQuestion: 'Another question',
    next: 'Next question',
    loading: 'Loading sounds…',
    replay: 'Replay',
    score: (right, asked) => `${right} / ${asked} correct`,
    right: 'Correct!',
    wrong: (answer) => `Not quite. It was: ${answer}.`,
    openApp: 'Practice more in the free app',
    names: {
      interval: {
        m2: 'minor 2nd', M2: 'major 2nd', m3: 'minor 3rd', M3: 'major 3rd', P4: 'perfect 4th', P5: 'perfect 5th',
        M6: 'major 6th', P8: 'octave',
      },
      chord: { major: 'major', minor: 'minor', diminished: 'diminished', augmented: 'augmented' },
      degree: { do: 'C (do)', re: 'D (re)', mi: 'E (mi)', fa: 'F (fa)', so: 'G (sol)', la: 'A (la)', ti: 'B (ti)' },
      pitch: { do: 'C', re: 'D', mi: 'E', fa: 'F', so: 'G', la: 'A', ti: 'B' },
    },
  },
}
