export function getChar() {
  // const emojis = ["😀", "🎉", "🚀", "✨", "🔥", "🍕", "🐱", "🌍", "💡", "🎶"];
  const emojis = [
    // Faces & Reactions
    "😀",
    "😁",
    "😊",
    "😎",

    // Celebration & Energy
    "🎉",
    "🥳",
    "✨",
    "🌟",
    "🔥",

    // Work & Ideas
    "💡",
    "📊",
    "💻",

    // Food & Fun
    "🍕",
    "☕",
    "🍩",
    "🍔",
    "🍪",
    "🥗",
    "🥤",

    //  Nature
    "🌞",
    "🌝",

    // Music & Creativity
    "🎶",
    "🎨",
    "🎤",
    "🎧",
  ];

  const randomIndex = Math.floor(Math.random() * emojis.length);
  return emojis[randomIndex];
}

export function getHeaderName(header) {
  const headerMap = {
    Category: "Domain",
    "Sub-Category": "Discipline",
    "Sub-Sub-Category": "Skill Area",
    Tools: "Framework",
    L1: "Basic",
    L2: "Intermediate",
    L3: "Expert",
    certProvider: "Cert. Provider",
    certName: "Certificate Name",
    certLevel: "Cert. Level",
    validYears: "Validity (in yrs)",
  };
  return headerMap[header] || header;
}
