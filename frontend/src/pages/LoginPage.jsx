import '@/index.css'
import { useState, useEffect } from 'react'
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import supabase from '@/lib/supabase/client'


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