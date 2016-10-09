"""
Here are the important views in a rough order that follows the path of a
submission:

* `Home` - where a user would learn about the service and hit 'apply'
* `SelectCounty` - a user selects the counties they need help with. This stores
    the county selection in the session.
* `CountyApplication` - a dynamic form built based on the county selection data
    that was stored in the session. This view does most of the validation work.
* `Confirm` (maybe) - if warnings exist on the form, users will be directed
    here to confirm their submission. Unlike errors, warnings do not prevent
    submission. This is just a slightly reduced version of `CountyApplication`.
* `Thanks` - a confirmation page that shows data from the newly saved
    submission.

A daily notification is sent to organizations with a link to a bundle of their
new applications.

* `ApplicationBundle` - This is typically the main page that organization users
    will access. Here they will see a collection of new applications, and, if
    needed, can see a filled pdf for their intake forms. If they need a pdf
    it will be served in an iframe by `FilledPDFBundle`
* `ApplicationIndex` - This is a list page that lets an org user see all the
    applications to their organization, organized in a table. Here they can
    access links to `ApplicationDetail` and `FilledPDF` for each app.
* `ApplicationDetail` - This shows the detail of one particular FormSubmission
"""
