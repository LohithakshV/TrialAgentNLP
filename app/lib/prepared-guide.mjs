export function applyPreparedGuide(result, prepared, profile) {
  const unchanged = prepared && JSON.stringify(prepared.profile) === JSON.stringify(profile);
  return unchanged ? { ...result, guide: prepared.guide, guideOrigin: 'ai' } : result;
}
