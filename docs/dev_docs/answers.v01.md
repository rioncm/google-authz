Do you already have a Google Workspace service account with domain-wide delegation configured, or should I stub the Admin SDK calls for now?

yes in private/gworkspace... Ultimatly it will be mounted via a k8 secret. 

Which exact user attributes and custom schema fields should we fetch for the EffectiveAuth prototype (field names, example values)?

I have created a custom set of attributes in addition to the standard attributes unders the grouping authorization 
- home department: single value
- user functions: multi-value
- Department Manager: bool

all standard attributes and the custom should be available ultimatly. 


Is there a preferred stack between FastAPI vs. “lightweight Python service scaffold” options, and any required Python version?
How should we supply local config (env vars, .env file, secret JSON) so the service can load credentials/config at runtime?
For the “hard-coded test endpoint” returning raw Workspace data plus EffectiveAuth, do you have a sample email we should use for manual testing?

FastApi all the way...