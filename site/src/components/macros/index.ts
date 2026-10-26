// The components that do what main.py's macros did for MkDocs, one import
// for every page that uses them: `import { Fact } from '~/components/macros'`.
//
//   {{ gate.promoted }}       <Fact of="gate.promoted" />
//   {{ feature_screen() }}    <FeatureScreen />    a feature page's first screen
//   {{ feature_plates() }}    <FeaturePlates />    the Features index
//   {{ board_reports() }}     <BoardReports />     data/boards.yaml as a table
//   {{ comparison_table() }}  <ComparisonTable />  reference/comparison's rows
//   {{ news_lede() }}         <NewsLede />         the newest post's lede
//   (the blog plugin)         <PostList />         the news index
export { default as Fact } from './Fact.astro';
export { default as FeatureScreen } from './FeatureScreen.astro';
export { default as FeaturePlates } from './FeaturePlates.astro';
export { default as BoardReports } from './BoardReports.astro';
export { default as ComparisonTable } from './ComparisonTable.astro';
export { default as NewsLede } from './NewsLede.astro';
export { default as PostList } from './PostList.astro';
