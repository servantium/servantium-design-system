/**
 * Steps — a short numbered sequence. Each number sits on the line of its step's title, with the
 * step's sentence underneath.
 *
 *   <Steps steps={[
 *     { title: "Invite your team", body: "Add people under Settings → Users." },
 *     { title: "Add your clients", body: "The accounts you do work for, under Clients." },
 *   ]} />
 *
 * For things done in order ("your first steps"). A list of things that aren't a sequence is Items.
 */
import { color, fonts } from '../theme';

export function Steps({ steps }: { steps: { title: string; body: string }[] }) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
      <tbody>
        {steps.map((st, i) => (
          <tr key={i}>
            <td width={40} valign="top" style={{ padding: i ? '16px 0 0' : '0' }}>
              <table role="presentation" cellPadding={0} cellSpacing={0} border={0}>
                <tbody><tr>
                  <td width={26} height={26} align="center" valign="middle" bgcolor={color.banner}
                    style={{ width: '26px', height: '26px', borderRadius: '13px', backgroundColor: color.banner, fontFamily: fonts.body,
                      fontSize: '13px', lineHeight: '26px', fontWeight: 700, color: color.onBanner }}>{i + 1}</td>
                </tr></tbody>
              </table>
            </td>
            <td valign="top" style={{ padding: i ? '16px 0 0' : '0' }}>
              <p style={{ margin: '1px 0 2px', fontFamily: fonts.body, fontSize: '16px', lineHeight: '24px', fontWeight: 700, color: color.ink }}>{st.title}</p>
              <p style={{ margin: 0, fontFamily: fonts.body, fontSize: '15px', lineHeight: '23px', color: color.ink }}>{st.body}</p>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
