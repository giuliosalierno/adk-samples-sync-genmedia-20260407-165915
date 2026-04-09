import TopNav from '../../components/TopNav'

function PipelineBuilder() {
  return (
    <div className="min-h-screen bg-gm-bg-light dark:bg-gm-bg flex flex-col">
      <TopNav />
      <div className="flex-1 relative">
        <iframe
          src="https://genmedia-pipes-demo-205784806851.us-central1.run.app/"
          className="w-full h-full absolute inset-0 border-0"
          title="Pipeline Builder"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        />
      </div>
    </div>
  )
}

export default PipelineBuilder
