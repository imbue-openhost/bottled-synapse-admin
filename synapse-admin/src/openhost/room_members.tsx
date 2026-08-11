// OpenHost fork: rooms are usually federated, so most members are remote users with no user page (see
// local_users.tsx). Upstream links every member to /users/<id> regardless, which bounces back to the
// user list. Remote members are rendered as plain rows here instead, and every member gets a kick
// button — removing someone from the room is the one administrative action the homeserver can take on
// a user it does not own.

import PersonRemoveIcon from "@mui/icons-material/PersonRemove";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import {
  Button,
  Confirm,
  Datagrid,
  FunctionField,
  Identifier,
  RaRecord,
  ReferenceField,
  ReferenceManyField,
  TextField,
  useListContext,
  useNotify,
  useRecordContext,
  useRefresh,
} from "react-admin";

import { RemoteUserChip, isLocalUser } from "./local_users";
import storage from "../storage";
import { jsonClient } from "../synapse/dataProvider";

async function kickFromRoom(roomId: Identifier, userId: Identifier): Promise<void> {
  const baseUrl = storage.getItem("base_url");
  if (!baseUrl) throw new Error("Homeserver not set");
  const endpoint = `${baseUrl}/_matrix/client/v3/rooms/${encodeURIComponent(roomId)}/kick`;
  await jsonClient(endpoint, { method: "POST", body: JSON.stringify({ user_id: userId }) });
}

interface MemberActionProps {
  roomId: Identifier;
  label?: string;
}

const RemoveMemberButton = ({ roomId }: MemberActionProps) => {
  const member = useRecordContext();
  const notify = useNotify();
  const refresh = useRefresh();
  const [confirming, setConfirming] = useState(false);

  const { mutate, isPending } = useMutation({
    mutationFn: () => kickFromRoom(roomId, member!.id),
    onSuccess: () => {
      setConfirming(false);
      notify(`Removed ${member!.id} from the room`);
      refresh();
    },
    onError: (error: Error) => {
      setConfirming(false);
      notify(`Could not remove ${member!.id}: ${error.message}`, { type: "error" });
    },
  });

  // Leaving is not an admin action; the logged-in user should do it from their own client.
  if (!member || member.id === storage.getItem("user_id")) return null;

  return (
    <>
      <Button label="Remove" onClick={() => setConfirming(true)} disabled={isPending}>
        <PersonRemoveIcon />
      </Button>
      <Confirm
        isOpen={confirming}
        loading={isPending}
        title="Remove from room"
        content={`Kick ${member.id} from this room? They can rejoin if the room allows it.`}
        onConfirm={() => mutate()}
        onClose={() => setConfirming(false)}
      />
    </>
  );
};

const BulkRemoveMembersButton = ({ roomId }: MemberActionProps) => {
  const { selectedIds, onUnselectItems } = useListContext();
  const notify = useNotify();
  const refresh = useRefresh();
  const [confirming, setConfirming] = useState(false);

  const { mutate, isPending } = useMutation({
    mutationFn: async () => {
      // Sequential: each kick is a state event in the same room, so concurrency just fights for the lock.
      for (const id of selectedIds) {
        await kickFromRoom(roomId, id);
      }
    },
    onSuccess: () => {
      setConfirming(false);
      notify(`Removed ${selectedIds.length} member(s) from the room`);
      onUnselectItems();
      refresh();
    },
    onError: (error: Error) => {
      setConfirming(false);
      notify(`Could not remove all selected members: ${error.message}`, { type: "error" });
      onUnselectItems();
      refresh();
    },
  });

  return (
    <>
      <Button label="Remove" onClick={() => setConfirming(true)} disabled={isPending}>
        <PersonRemoveIcon />
      </Button>
      <Confirm
        isOpen={confirming}
        loading={isPending}
        title="Remove from room"
        content={`Kick ${selectedIds.length} selected member(s) from this room?`}
        onConfirm={() => mutate()}
        onClose={() => setConfirming(false)}
      />
    </>
  );
};

export const RoomMembers = () => {
  const room = useRecordContext();
  if (!room) return null;

  return (
    <ReferenceManyField reference="room_members" target="room_id" label={false}>
      <Datagrid
        style={{ width: "100%" }}
        rowClick={id => (isLocalUser(id) ? `/users/${id}` : false)}
        bulkActionButtons={<BulkRemoveMembersButton roomId={room.id} />}
      >
        <TextField source="id" sortable={false} label="resources.users.fields.id" />
        <FunctionField
          label="resources.users.fields.displayname"
          sortable={false}
          render={(member: RaRecord) =>
            isLocalUser(member.id) ? (
              <ReferenceField source="id" reference="users" link="">
                <TextField source="displayname" />
              </ReferenceField>
            ) : (
              <RemoteUserChip userId={member.id} />
            )
          }
        />
        <RemoveMemberButton roomId={room.id} label="" />
      </Datagrid>
    </ReferenceManyField>
  );
};
