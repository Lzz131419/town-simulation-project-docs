export function renderProfile(element, agent) {
 element.textContent = agent.sourceType==='digitalPerson'
  ? `已授权数字人物 · ${agent.displayName}\n${agent.profile.bioSummary??''}\n姓名用于显示；职业参与共同规则；授权勾选不等于身份认证。`
  : `生成居民 · ${agent.displayName}`;
}
