// Supabase Edge Function for AI Panel Analytics
// Deploy this to: Supabase Dashboard → Edge Functions → ai-panel-analytics

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-api-key',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // 1. API Key Authentication - First line of defense
    // Check Authorization header (format: "Bearer <key>")
    const authHeader = req.headers.get('authorization')
    const apiKey = authHeader?.replace('Bearer ', '')
    const validApiKey = Deno.env.get('ANALYTICS_API_KEY')

    // Debug logging
    console.log('[Auth Debug] Authorization Header:', authHeader || 'MISSING')
    console.log('[Auth Debug] Extracted API Key:', apiKey || 'MISSING')
    console.log('[Auth Debug] Expected API Key:', validApiKey || 'MISSING')
    console.log('[Auth Debug] Keys match:', apiKey === validApiKey)

    if (!apiKey || !validApiKey || apiKey !== validApiKey) {
      console.error('[Auth] API key validation failed')
      return new Response(
        JSON.stringify({
          error: 'Unauthorized - Invalid API key',
          debug: {
            receivedKey: apiKey ? 'present' : 'missing',
            expectedKey: validApiKey ? 'present' : 'missing'
          }
        }),
        {
          status: 401,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // 2. Get client IP for rate limiting
    const clientIP = req.headers.get('cf-connecting-ip') ||
                     req.headers.get('x-forwarded-for') ||
                     'unknown'

    // 3. Parse request body
    const payload = await req.json()

    // 4. Validate required fields
    if (!payload.first_install_date || !payload.platform) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // 5. Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // 6. IP-based rate limiting: Max 10 requests per hour from same IP
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString()
    const { count: ipRequestCount } = await supabaseClient
      .from('ai_panel_analytics')
      .select('*', { count: 'exact', head: true })
      .eq('client_ip', clientIP)
      .gte('created_at', oneHourAgo)

    if (ipRequestCount && ipRequestCount >= 10) {
      console.log(`[Rate Limit] IP ${clientIP} exceeded 10 requests/hour`)
      return new Response(
        JSON.stringify({ error: 'Rate limit exceeded' }),
        {
          status: 429,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // 7. Upsert analytics data (update existing row or insert new)
    // Unique constraint on first_install_date ensures 1 row per user
    const { data, error } = await supabaseClient
      .from('ai_panel_analytics')
      .upsert(
        {
          first_install_date: payload.first_install_date,
          platform: payload.platform,
          locale: payload.locale,
          timezone: payload.timezone,
          total_uses: payload.total_uses,
          active_days: payload.active_days,
          days_since_install: payload.days_since_install,
          retention_rate: payload.retention_rate,
          has_logged_in: payload.has_logged_in,
          signup_method: payload.signup_method,
          auth_button_clicked: payload.auth_button_clicked,
          last_used_date: payload.last_used_date,
          client_ip: clientIP,
          // Onboarding & Tutorial
          onboarding_completed: payload.onboarding_completed,
          tutorial_status: payload.tutorial_status,
          tutorial_current_step: payload.tutorial_current_step,
          // Usage tracking
          quick_action_usage_count: payload.quick_action_usage_count,
          shortcut_usage_count: payload.shortcut_usage_count,
        },
        {
          onConflict: 'first_install_date',  // Unique key
          ignoreDuplicates: false  // Always update
        }
      )

    if (error) {
      console.error('[Database] Insert error:', error)
      throw error
    }

    console.log('[Success] Analytics recorded for IP:', clientIP)

    return new Response(
      JSON.stringify({ success: true, message: 'Analytics recorded' }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('[Error]', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})
