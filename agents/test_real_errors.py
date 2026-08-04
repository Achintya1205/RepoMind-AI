from agents.debug.debug_agent import DebugAgent


agent = DebugAgent()


errors = [

"""
Traceback (most recent call last):
 File "sample_repos/bulletproof-react/apps/react-vite/src/lib/api-client.ts", line 12, in authRequestInterceptor
 Error: Authentication failed
""",


"""
Traceback (most recent call last):
 File "sample_repos/bulletproof-react/apps/nextjs-app/src/utils/auth.ts", line 15, in checkLoggedIn
 Error: Invalid token
""",


"""
Error: Cannot read property 'data'

at getUsers (sample_repos/bulletproof-react/apps/react-vite/src/features/users/api/get-users.ts:20:5)
at UsersPage (sample_repos/bulletproof-react/apps/react-vite/src/app/routes/app/users.tsx:10:3)
"""

]


for error in errors:

    print("\n====================")

    result = agent.analyze(error)

    print(result)