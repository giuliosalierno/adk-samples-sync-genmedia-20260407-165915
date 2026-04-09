import TopNav from '../components/TopNav'

function Projects() {
  return (
    <div className="min-h-screen bg-gm-bg-light dark:bg-gm-bg">
      <TopNav />

      <main className="h-[calc(100vh-73px)]">
        <iframe
          src="https://genmedia-pipes-205784806851.us-central1.run.app/"
          title="GenMedia Pipes"
          className="w-full h-full border-0"
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
        />
      </main>
    </div>
  )
}

export default Projects
