// OpenHost fork: Synapse's admin API only knows users local to the homeserver you are logged into
// ("Can only look up local users"). Anywhere upstream links a Matrix ID to /users/<id>, a federated ID
// produces a page whose getOne fails and which react-admin then bounces back to the user list. These
// helpers keep those links pointed only at users the admin API can actually serve.

import Chip from "@mui/material/Chip";
import { Identifier, RaRecord, ReferenceField, TextField, useRecordContext } from "react-admin";

import storage from "../storage";

export const isLocalUser = (userId: Identifier) => String(userId).endsWith(`:${storage.getItem("home_server")}`);

export const serverOf = (userId: Identifier) => String(userId).split(":").slice(1).join(":");

export const RemoteUserChip = ({ userId }: { userId: Identifier }) => (
  <Chip size="small" variant="outlined" label={serverOf(userId)} />
);

interface UserIdFieldProps {
  source: string;
  label?: string;
  sortable?: boolean;
}

// Renders a Matrix ID: a link to the user page for local users, plain text plus the origin server for
// federated ones, which have no user page.
export const UserIdField = ({ source }: UserIdFieldProps) => {
  const record = useRecordContext<RaRecord>();
  const userId = record?.[source] as Identifier | undefined;
  if (!userId) return null;

  if (!isLocalUser(userId)) {
    return (
      <>
        {userId} <RemoteUserChip userId={userId} />
      </>
    );
  }
  return (
    <ReferenceField source={source} reference="users">
      <TextField source="id" />
    </ReferenceField>
  );
};
