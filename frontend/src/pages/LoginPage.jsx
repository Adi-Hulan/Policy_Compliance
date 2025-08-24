import '@/index.css'
  import { useState, useEffect } from 'react'
  import { createClient } from '@supabase/supabase-js'
  import { Auth } from '@supabase/auth-ui-react'
  import { ThemeSupa } from '@supabase/auth-ui-shared'
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
  const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

  console.log(supabaseUrl, supabaseAnonKey)
  const supabase = createClient(supabaseUrl, supabaseAnonKey)

  export default function App() {
    const [session, setSession] = useState(null)

    useEffect(() => {
      supabase.auth.getSession().then(({ data: { session } }) => {
        setSession(session)
      })

      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange((_event, session) => {
        setSession(session)
      })

      return () => subscription.unsubscribe()
    }, [])

    if (!session) {
      return (
        <div>
          <Auth supabaseClient={supabase} appearance={{ theme: ThemeSupa }} />
        </div>
      )
    }
    else {
      return (
        <div>
            <p>test</p>
          <h2>Logged in!</h2>
          <p>Session: {JSON.stringify(session, null, 2)}</p>
          <button onClick={() => supabase.auth.signOut()} style={{ padding: '10px', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Sign Out
          </button>
        </div>
      )
    }
  }