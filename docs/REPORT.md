# Automated Reports in TaxBrain

As of release 2.3.0, the `taxbrain` package has the ability to automatically
generate reports summarizing the effects of a user specified policy reform.

To generate these reports, Tax-Brain starts with an initialized `TaxBrain`
object and uses its attributes – such as the reform and data associated with the
object – and complies them based on a given template. In the basic template
included with the `taxbrain` package (written by Anderson Frailey), the report
will include information on total changes in tax liability, which groups are
most affected by the given policy, and a few graphs.